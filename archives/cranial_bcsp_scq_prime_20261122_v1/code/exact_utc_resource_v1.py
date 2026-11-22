"""One read-only system resource exception. All other paths remain unhandled."""
import hashlib
import os
import stat
from pathlib import Path

UTC_RESOURCE = dict(link='/usr/share/zoneinfo/UTC', link_text='Etc/UTC',
                    target='/usr/share/zoneinfo/Etc/UTC', bytes=118,
                    sha256='ab1ddb33c7187e56408033a8165ea3b1432e024710e7ab2aafec036a8bd7f09a')


def require(value, text):
    if not value:
        raise RuntimeError(text)


def inspect_binding(binding):
    link, target = Path(binding['link']), Path(binding['target'])
    ls, ts = link.lstat(), target.lstat()
    return dict(link_is_symlink=stat.S_ISLNK(ls.st_mode), link_text=os.readlink(link),
                resolved_target=str(link.resolve(strict=True)), target_is_regular=stat.S_ISREG(ts.st_mode),
                target_has_link_ancestor=any(p.is_symlink() for p in (target, *target.parents)),
                link_has_link_ancestor=any(p.is_symlink() for p in link.parents),
                bytes=ts.st_size, device=ts.st_dev, inode=ts.st_ino)


def validate_metadata(binding, observed):
    require(set(binding)=={'link','link_text','target','bytes','sha256'}, 'exact resource fields')
    require(observed['link_is_symlink'] and observed['link_text']==binding['link_text'], 'UTC link drift')
    require(observed['resolved_target']==binding['target'], 'UTC resolved target drift')
    require(observed['target_is_regular'] and not observed['target_has_link_ancestor']
            and not observed['link_has_link_ancestor'], 'UTC target/ancestor link drift')
    require(observed['bytes']==binding['bytes'], 'UTC target size drift')


class ExactUTCReader:
    def __init__(self, binding):
        self.binding = dict(binding)
        observed = inspect_binding(self.binding)
        validate_metadata(self.binding, observed)
        # Open before installing the audit hook. Future verification reads this
        # read-only fd, avoiding recursive open->audit->open exception handling.
        self.fd = os.open(self.binding['target'], os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        self.read_checks = 0
        try:
            self.verify()
        except BaseException:
            self.close()
            raise

    def verify(self):
        require(self.fd is not None, 'resource fd closed')
        before = inspect_binding(self.binding)
        validate_metadata(self.binding, before)
        fdstat = os.fstat(self.fd)
        require((fdstat.st_dev, fdstat.st_ino, fdstat.st_size)==
                (before['device'], before['inode'], self.binding['bytes']), 'UTC file replaced')
        os.lseek(self.fd, 0, os.SEEK_SET)
        data = os.read(self.fd, self.binding['bytes'] + 1)
        require(len(data)==self.binding['bytes'] and hashlib.sha256(data).hexdigest()==self.binding['sha256'],
                'UTC target content drift')
        after = inspect_binding(self.binding)
        validate_metadata(self.binding, after)
        require(before==after, 'UTC metadata changed during verification')
        self.read_checks += 1

    def allow(self, filename, write=False):
        if isinstance(filename, int):
            return False
        # Exact spellings only. No directory/pattern or generic symlink allowance.
        if os.fsdecode(filename) not in (self.binding['link'], self.binding['target']):
            return False
        require(not write, 'UTC resource write denied')
        self.verify()
        return True

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
