"""One authorized materialization and tmux launch; no retry or scientific changes."""
import base64, datetime, hashlib, json, os, shlex, shutil, socket, stat, subprocess, time
from pathlib import Path
SCOPE_SHA = '1614cd0bf883b8a700a633d3a8fe5f21981f5a3f9c9729bf36ab19b0d89bd7ed'
SCOPE_RAW = "{\n  \"schema\": \"bcsp-first-run-training-execution-scope-v1\",\n  \"status\": \"AWAITING_EXPLICIT_USER_AUTHORIZATION\",\n  \"date_Asia_Shanghai\": \"2026-10-25\",\n  \"execution_authorized\": false,\n  \"request_kind\": \"Single first real training run, not a new implementation or GPU preflight\",\n  \"run_id\": \"bcsp_geov1_b0_foldC_in8192_out8192_seed0_train_v1\",\n  \"entry_interface_schema\": \"bcsp-training-request-v2\",\n  \"first_training_attempt_not_previously_started\": true,\n  \"entry_request\": {\n    \"path\": \"E:\\\\Codex\\\\2026-06-06\\\\mamba-ccf-c-1-high-resolution\\\\outputs\\\\cranial_bcsp_geov1_20261024\\\\resource_rebind_implementation_v1\\\\first_training_request_foldC_8192_v1\\\\training_entry_request_v2.json\",\n    \"bytes\": 5370,\n    \"sha256\": \"aaa92444334ec61d57f593d51f983e79db1aa4d954d15a487b715e911e34dbc9\",\n    \"future_server_path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/training_execution_request_v1.json\"\n  },\n  \"migration_acceptance\": {\n    \"path\": \"E:\\\\Codex\\\\2026-06-06\\\\mamba-ccf-c-1-high-resolution\\\\outputs\\\\cranial_bcsp_geov1_20261024\\\\resource_rebind_implementation_v1\\\\first_training_request_foldC_8192_v1\\\\migration_uncertainty_acceptance_v1.json\",\n    \"bytes\": 2259,\n    \"sha256\": \"28588c5ea4d5ad14cdb60f1e8fc52f9474629230ef1150c11f61888322a20527\",\n    \"future_server_path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/migration_uncertainty_acceptance_v1.json\"\n  },\n  \"new_gpu_execution_validated\": false,\n  \"historical_GPU_evidence_only\": true,\n  \"parent_evidence\": {\n    \"post_installation_freeze_audit\": {\n      \"path\": \"E:\\\\Codex\\\\2026-06-06\\\\mamba-ccf-c-1-high-resolution\\\\outputs\\\\cranial_bcsp_geov1_20261024\\\\resource_rebind_implementation_v1\\\\authorized_installation_v2\\\\post_installation_freeze_audit_v1\\\\post_installation_freeze_audit_report_v1.json\",\n      \"bytes\": 173511,\n      \"sha256\": \"d91302e1c360bf56323c4ae2dedc7605b6a80dce1b8816ca552b0c2ea6577fb4\"\n    },\n    \"contract_resource_review\": {\n      \"path\": \"E:\\\\Codex\\\\2026-06-06\\\\mamba-ccf-c-1-high-resolution\\\\outputs\\\\cranial_bcsp_geov1_20261024\\\\resource_rebind_implementation_v1\\\\first_run_contract_resource_review_v1\\\\first_run_contract_resource_migration_review_v1.json\",\n      \"bytes\": 15295,\n      \"sha256\": \"9cb6af6512867f13b1b9acc176a73c2682ea17b155969d720f4e0fb7614f0c56\"\n    },\n    \"resource_rebind\": {\n      \"path\": \"E:\\\\Codex\\\\2026-06-06\\\\mamba-ccf-c-1-high-resolution\\\\outputs\\\\cranial_bcsp_geov1_20261024\\\\resource_rebind_implementation_v1\\\\resource_rebind_receipt_v1.json\",\n      \"bytes\": 3601,\n      \"sha256\": \"11afc76b0a130f5c6a6c5a28fb147e7ab7d144cddb55c213f9f3ab3dc07c33b0\"\n    },\n    \"implementation_P3\": {\n      \"path\": \"E:\\\\Codex\\\\2026-06-06\\\\mamba-ccf-c-1-high-resolution\\\\outputs\\\\cranial_bcsp_geov1_20261024\\\\resource_rebind_implementation_v1\\\\local_P3_receipt_v1.json\",\n      \"bytes\": 26625,\n      \"sha256\": \"2954424b806c37a9262f5c57a357e5b9105fe0e972e80e3a614bc866d55a1b36\"\n    },\n    \"installed_scope\": {\n      \"path\": \"E:\\\\Codex\\\\2026-06-06\\\\mamba-ccf-c-1-high-resolution\\\\outputs\\\\cranial_bcsp_geov1_20261024\\\\resource_rebind_implementation_v1\\\\readonly_installation_readiness_v1\\\\combined_no_overwrite_installation_scope_v1.json\",\n      \"bytes\": 232620,\n      \"sha256\": \"42d0b302e40ec0d127c147063b0df9ddd662aa1ef37d964387dd3c8081cd6e62\"\n    }\n  },\n  \"scientific_contract\": {\n    \"stage\": \"BCSP_INPUT_DENSITY_V1\",\n    \"baseline\": \"B0 AdaPoinTr Transformer; not Mamba/SCQR\",\n    \"fold\": \"C\",\n    \"seed\": 0,\n    \"input_points\": 8192,\n    \"target_points\": 8192,\n    \"sources\": 63,\n    \"cases\": 315,\n    \"defects_per_source\": 5,\n    \"batch\": 8,\n    \"epochs\": 100,\n    \"epoch_labels\": [\n      0,\n      99\n    ],\n    \"batches_per_epoch\": 39,\n    \"optimizer_updates\": 3900,\n    \"case_exposures\": 31200,\n    \"dropped_exposures\": 300,\n    \"drop_last\": true,\n    \"step_per_update\": 1,\n    \"scratch\": true,\n    \"final_only\": true,\n    \"precision\": \"FP32\",\n    \"deterministic\": true,\n    \"TF32\": false,\n    \"AMP\": false,\n    \"optimizer\": {\n      \"seed\": 0,\n      \"precision\": \"FP32\",\n      \"optimizer\": \"AdamW\",\n      \"lr\": 0.0001,\n      \"weight_decay\": 0.0005,\n      \"clip\": 10,\n      \"step_per_update\": 1,\n      \"drop_last\": true,\n      \"checkpoint\": \"scratch_final_only\",\n      \"BNCal\": false,\n      \"evaluation\": false,\n      \"resume\": false\n    },\n    \"LR_scheduler\": \"max(0.9**(e/21),0.02) after each epoch,100 calls\",\n    \"BN_scheduler\": \"ordinary training BN tracks running stats; momentum=max(0.9*0.5**(e/21),0.01) at epoch start,100 calls\",\n    \"KNN\": \"Full keys,query chunk256,no key truncation\",\n    \"PointNet2\": \"Existing fixed cp310 native provider\",\n    \"Chamfer\": \"Existing torch.cdist branch; no installed/compiled Chamfer swap\",\n    \"static_config\": {\n      \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/static_training_config_v1.json\",\n      \"bytes\": 2024,\n      \"sha256\": \"86dbbb7b216a932209abd446bdd28408ad5327433834336f2584b087c1b35647\"\n    },\n    \"order_plan\": {\n      \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/shared_order_foldC_seed0_v1.json\",\n      \"bytes\": 1248506,\n      \"sha256\": \"6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d\"\n    },\n    \"qualified_QC\": {\n      \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/qualified_data_qc_foldC_8192_v1.json\",\n      \"bytes\": 1659,\n      \"sha256\": \"1f574ad3f4eff4c6dc70f6065432705aa3286819f1637801f506afc8916799aa\"\n    },\n    \"training_runtime\": {\n      \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_training_runtime_v5.py\",\n      \"bytes\": 10171,\n      \"sha256\": \"55ad69b0e87f3fc4ecac68a5ebcc4cdd560c4825ff01363ba9868de5875f0847\"\n    },\n    \"real_payload_scope\": \"Only315 exact FoldC training NPZ files in installed337 map; no new/confirmation/development payload access\",\n    \"anatomical_semantic_limits\": [\n      \"Separate inner/outer plate coverage not certified\",\n      \"Representation QC is not prediction or clinical accuracy\",\n      \"Artificial GPU zero-update success is not complete training memory proof\"\n    ]\n  },\n  \"resources_unchanged\": {\n    \"static\": {\n      \"wall_seconds\": 86400,\n      \"RSS_bytes\": 8589934592,\n      \"device_MiB\": 22528,\n      \"torch_peak_bytes\": 21474836480,\n      \"output_bytes\": 2147483648,\n      \"minimum_free_disk_bytes\": 4294967296\n    },\n    \"GPU_initial_used_MiB_at_most\": 256,\n    \"require_no_other_compute_processes\": true,\n    \"threads\": 2,\n    \"loader_workers\": 0,\n    \"external_timeout_seconds\": 86400,\n    \"kill_grace_seconds\": 5,\n    \"max_resource_records\": 3902,\n    \"SMI_query_seconds\": 10,\n    \"SMI_reap_seconds\": 2,\n    \"limits\": \"Monitored/cooperative resource stopping, not exclusive cgroup/hard continuous-memory isolation. /proc/meminfo andcpu_count are recorded host-visible observations, not dedicated allocations.\"\n  },\n  \"environment\": {\n    \"CUDA_VISIBLE_DEVICES\": \"GPU-4b19574a-832d-b4fe-e655-a57462954d6a\",\n    \"CUBLAS_WORKSPACE_CONFIG\": \":4096:8\",\n    \"OMP_NUM_THREADS\": \"2\",\n    \"MKL_NUM_THREADS\": \"2\",\n    \"OPENBLAS_NUM_THREADS\": \"2\",\n    \"PYTHONDONTWRITEBYTECODE\": \"1\",\n    \"MPLBACKEND\": \"Agg\",\n    \"MPLCONFIGDIR\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/mplconfig\",\n    \"CUDA_CACHE_DISABLE\": \"1\",\n    \"TMPDIR\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/tmp\"\n  },\n  \"resource_snapshot_evidence\": {\n    \"UTC\": \"2026-10-25T14:03:05.400570+00:00\",\n    \"gates\": {\n      \"GPU_idle_at_most256MiB\": true,\n      \"no_GPU_compute_processes\": true,\n      \"free_disk_at_least4GiB\": true,\n      \"fixed_python_identity\": true,\n      \"fresh_owned_output_and_control\": true,\n      \"unused_tmux_session\": true\n    },\n    \"disk_free_GiB\": 13.08203125,\n    \"not_persistent_admission\": true,\n    \"recheck_before_launch\": true\n  },\n  \"future_paths\": {\n    \"execution_scope\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/training_execution_scope_v1.json\",\n    \"migration_acceptance\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/migration_uncertainty_acceptance_v1.json\",\n    \"entry_request\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/training_execution_request_v1.json\",\n    \"authorization\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/training_authorization_v1.json\",\n    \"runtime\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/training_runtime_v1.json\",\n    \"launcher\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/train_once_v1.sh\",\n    \"launch_attempt\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/launch_attempt_v1.json\",\n    \"tmux_session\": \"bcsp_geov1_b0_foldc_in8192_seed0_train_v1\",\n    \"output\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1\",\n    \"log\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/launch.log\",\n    \"worker_pid\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/worker.pid\",\n    \"exit_code\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/exit_code.txt\",\n    \"final_checkpoint\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/ckpt-last.pth\",\n    \"completion\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/completion.json\",\n    \"failure\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/failure.json\",\n    \"startup_failure\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/startup_failure.json\",\n    \"metrics\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/metrics.jsonl\",\n    \"resources\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/resources.jsonl\",\n    \"exposure\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/exposure.json\",\n    \"order_copy\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1/order_plan.json\"\n  },\n  \"future_materialization_contract\": {\n    \"requires_separate_user_authorization_of_full_execution_scope_SHA256\": true,\n    \"no_materialization_performed_now\": true,\n    \"strict_entry_compatibility\": \"Entry request remains exact installed bcsp-training-request-v2 schema. This execution scope and acceptance are caller-reviewed metadata; installed entry does not parse this envelope. Authorized materializer must verify full envelope hash, exact inner request/acceptance hashes and all frozen fields before any launch.\",\n    \"one_way_order\": [\n      \"Verify this execution scope fullSHA and bound entry_request / migration_acceptance / prior evidence; refresh metadata/resource/source/QC guards without model calls\",\n      \"Create exact pending-scope,acceptance and strict-entry-request copies without overwrites under control; all remain metadata until full authorization\",\n      \"Create separate training authorization binding strict entry_request SHA and exact user grant text naming this scope SHA; no runtime-config hash\",\n      \"Compute authorization SHA,then create runtime JSON binding strict entry_request SHA and authorization SHA only\",\n      \"Create exclusive single launcher,verify its frozen argument/environment/timeout contract\",\n      \"Create exclusive launch_attempt with strict entry_request SHA and CLAIMED_BEFORE_TMUX before the one tmux launch; any tmux failure consumes attempt,never retry\"\n    ],\n    \"authorization_schema\": {\n      \"schema\": \"bcsp-training-authorization-v1\",\n      \"request_sha256\": \"aaa92444334ec61d57f593d51f983e79db1aa4d954d15a487b715e911e34dbc9\",\n      \"explicit_user_authorization\": \"Must become true only after a new explicit grant of this scope full SHA\",\n      \"user_authorization_text\": \"Exact future user grant text; include execution scope SHA and inner request SHA context; no fabrication\"\n    },\n    \"runtime_schema\": {\n      \"schema\": \"bcsp-training-runtime-v1\",\n      \"request_sha256\": \"aaa92444334ec61d57f593d51f983e79db1aa4d954d15a487b715e911e34dbc9\",\n      \"authorization_sha256\": \"Computed only after real authorization file exists; not reverse-bound by authorization\"\n    },\n    \"launcher_rules\": [\n      \"Verify all authorization/runtime links before invoking entry; exact record hashes and frozen schemas, no extra fields\",\n      \"Recheck project identity,no links,unused tmux/control launch_attempt and nonexistent owned result before launch\",\n      \"Create and verify log parent before redirecting; entry must see fresh output containing only launch.log, then creates worker PID/resources/tmp itself\",\n      \"Use only frozen inherited environment plus new exact UUID and owned TMPDIR; no model/backend/threshold changes\",\n      \"Call the exact external timeout parent and Python -I -S -B argv below; retain request/authorization/runtime exact hashes\",\n      \"Record child return code in frozen exit_code.txt and propagate it; PowerShell caller must explicitly exit $LASTEXITCODE, raw stdout/stderr byte capture\",\n      \"Verify actual startup/session/PID or immediate exit; shell/client rc0 alone is not launch/training success. On ambiguous connection loss stop,do not launch again\"\n    ],\n    \"external_training_argv\": [\n      \"/usr/bin/timeout\",\n      \"--signal=TERM\",\n      \"--kill-after=5s\",\n      \"86400s\",\n      \"/opt/conda/envs/adapointr-mamba/bin/python3.10\",\n      \"-I\",\n      \"-S\",\n      \"-B\",\n      \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_training_entry_v2.py\",\n      \"--request\",\n      \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/training_execution_request_v1.json\",\n      \"--request-sha256\",\n      \"aaa92444334ec61d57f593d51f983e79db1aa4d954d15a487b715e911e34dbc9\",\n      \"--authorization\",\n      \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/training_authorization_v1.json\",\n      \"--authorization-sha256\",\n      \"<computed_authorization_SHA256>\",\n      \"--runtime\",\n      \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/training_runtime_v1.json\",\n      \"--runtime-sha256\",\n      \"<computed_runtime_SHA256>\"\n    ]\n  },\n  \"prelaunch_guards\": [\n    \"Exact current hostname/uid/project/Python/new GPU UUID/model/capacity/driver; any new resource identity difference stops,not auto-rebound\",\n    \"Recheck installed implementation/QC/config/order/data and existing frozen model/provider/environment bindings,using exact scopes; no broad inventory expansion or dependency downloads\",\n    \"Current GPU memory<=256MiB,no other compute processes,disk>=4GiB,all resource ceilings unchanged\",\n    \"Frozen source/fold315-case allowlist and authoritative shared_order file; do not regenerate random order\",\n    \"Output/control execution artifacts,tmux session and launch marker must be fresh/exclusive; never overwrite\",\n    \"New-device acceptance is only acceptance of uncertainty; never change new_gpu_execution_validated to true or substitute historical GPU report\"\n  ],\n  \"failure_policy\": {\n    \"stop_immediately\": true,\n    \"automatic_retry\": false,\n    \"resume\": false,\n    \"automatic_batch_or_precision_reduction\": false,\n    \"backend_fallback\": false,\n    \"parameter_or_case_scan\": false,\n    \"automatic_new_GPU_preflight\": false,\n    \"BNCal\": false,\n    \"development_evaluation\": false,\n    \"followup_training_runs\": false,\n    \"retain_partial_files_and_committed_step_counts\": true,\n    \"no_automatic_cleanup\": true,\n    \"timeout_or_ambiguous_start\": \"Attempt consumed; inspect only under appropriate authorization before considering a new request.\"\n  },\n  \"success_requires\": {\n    \"training_exit_code\": 0,\n    \"forward\": 3900,\n    \"backward\": 3900,\n    \"clip\": 3900,\n    \"optimizer_step\": 3900,\n    \"LR_scheduler_calls\": 100,\n    \"BN_scheduler_calls\": 100,\n    \"case_exposures\": 31200,\n    \"final_checkpoint_SHA256\": true,\n    \"BNCal\": false,\n    \"development_evaluation\": false,\n    \"resume\": false,\n    \"post_training_freeze_audit\": \"Separate explicit authorization required; no automatic next-stage training/BNCal/evaluation\"\n  },\n  \"current_task_boundary\": {\n    \"files_created\": \"Pending execution scope,strict entry request,and migration acceptance metadata only,on Windows normative workspace\",\n    \"server_operations\": 0,\n    \"runtime_config_created\": false,\n    \"launcher_created\": false,\n    \"training_execution_authorization_created\": false,\n    \"launch_attempt_created\": false,\n    \"tests\": 0,\n    \"GPU_calls\": 0,\n    \"training_steps\": 0\n  },\n  \"provenance_path_note\": \"Windows paths in evidence records are local provenance only. Never convert or execute them on server. Only future_server_path/future_paths/strict request server paths define permitted remote paths.\",\n  \"next\": \"Await separate explicit user authorization of this execution scope full SHA256. Neither accepting migration uncertainty nor creating this pending request authorizes execution.\"\n}\n".encode('utf-8')
Q_RAW = "{\n  \"schema\": \"bcsp-training-request-v2\",\n  \"stage\": \"BCSP_INPUT_DENSITY_V1\",\n  \"status\": \"AWAITING_EXPLICIT_USER_AUTHORIZATION\",\n  \"run_id\": \"bcsp_geov1_b0_foldC_in8192_out8192_seed0_train_v1\",\n  \"fold\": \"C\",\n  \"n_input\": 8192,\n  \"static_config\": {\n    \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/static_training_config_v1.json\",\n    \"bytes\": 2024,\n    \"sha256\": \"86dbbb7b216a932209abd446bdd28408ad5327433834336f2584b087c1b35647\"\n  },\n  \"QC\": {\n    \"qualified_receipt\": {\n      \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/qualified_data_qc_foldC_8192_v1.json\",\n      \"bytes\": 1659,\n      \"sha256\": \"1f574ad3f4eff4c6dc70f6065432705aa3286819f1637801f506afc8916799aa\"\n    },\n    \"verification\": {\n      \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/real_data_qc_verification_v1.json\",\n      \"bytes\": 5769,\n      \"sha256\": \"54fcd0018f9a51f04b8408b3842b6d5c4243777979a0e0add31541e04fa3c55b\"\n    },\n    \"manifests\": {\n      \"8192\": {\n        \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/manifest_8192.jsonl\",\n        \"bytes\": 427975,\n        \"sha256\": \"f94dbe21cb9e406db49a51f6578496db3228d783f15c07b28e3d8ae234a33758\"\n      },\n      \"16384\": {\n        \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/manifest_16384.jsonl\",\n        \"bytes\": 428815,\n        \"sha256\": \"1cd06c7d3b33191d02b5464e72fd83ba4b38c839c0bb4da865bed374076734b5\"\n      }\n    },\n    \"fold_binding\": {\n      \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/fold_binding.json\",\n      \"bytes\": 35012,\n      \"sha256\": \"cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90\"\n    }\n  },\n  \"order_plan\": {\n    \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/shared_order_foldC_seed0_v1.json\",\n    \"bytes\": 1248506,\n    \"sha256\": \"6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d\"\n  },\n  \"GPU_audit\": {\n    \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/post_preflight_freeze_audit_report_v1.json\",\n    \"bytes\": 31109,\n    \"sha256\": \"af3c3053be96a443d203c486ccede4d2bf2f0799ae753294ee946618726cf000\"\n  },\n  \"preflight_request_sha256\": \"7a7a74fcec86bb4fa6c7ab77b74e8d509a26ae75ade73a05d9c8cab183ef2365\",\n  \"preflight_scope\": {\n    \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/evidence/frozen_scope_v3.json\",\n    \"bytes\": 23220,\n    \"sha256\": \"c6edb9bfcf833d2abf98eb18749d03b49a490579d79475e4823750df6a8311e6\"\n  },\n  \"identity\": {\n    \"hostname\": \"shu-common-25721452-notebook-3x9rq5-0\",\n    \"uid\": 1000,\n    \"project\": \"/home/jovyan/adapointr_work/PoinTr\",\n    \"gpu_uuid\": \"GPU-4b19574a-832d-b4fe-e655-a57462954d6a\",\n    \"gpu_name\": \"NVIDIA GeForce RTX 4090 D\",\n    \"driver_version\": \"570.190\",\n    \"nvidia_smi_memory_total_MiB\": 24564,\n    \"python_realpath\": \"/opt/conda/envs/adapointr-mamba/bin/python3.10\",\n    \"python_version\": \"3.10.20\",\n    \"torch_version\": \"2.4.1+cu118\",\n    \"numpy_version\": \"2.2.6\",\n    \"timm_version\": \"1.0.27\",\n    \"memory_query_semantics\": \"SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.\"\n  },\n  \"data_root\": \"/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1\",\n  \"model_root\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3\",\n  \"implementation\": {\n    \"entry\": {\n      \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_training_entry_v2.py\",\n      \"bytes\": 14714,\n      \"sha256\": \"eb2f2f0f53aa9e36636e576dc3e25b4fee86df276eb476e79f5f1e1bee804852\"\n    },\n    \"contract\": {\n      \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_training_contract_v2.py\",\n      \"bytes\": 16538,\n      \"sha256\": \"88b0098ec199fcba7e37c9ca2be7a8d6b69ff246ab0f1b9494445e4a72b41db3\"\n    },\n    \"runtime\": {\n      \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_training_runtime_v5.py\",\n      \"bytes\": 10171,\n      \"sha256\": \"55ad69b0e87f3fc4ecac68a5ebcc4cdd560c4825ff01363ba9868de5875f0847\"\n    },\n    \"preflight_helper\": {\n      \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/bcsp_artificial_gpu_preflight_v3.py\",\n      \"bytes\": 32728,\n      \"sha256\": \"7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291\"\n    }\n  },\n  \"output\": \"/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1\",\n  \"launch_attempt\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control/launch_attempt_v1.json\",\n  \"resource_rebind\": {\n    \"path\": \"/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/resource_rebind_receipt_v1.json\",\n    \"bytes\": 3601,\n    \"sha256\": \"11afc76b0a130f5c6a6c5a28fb147e7ab7d144cddb55c213f9f3ab3dc07c33b0\"\n  }\n}\n".encode('utf-8')
ACCEPT_RAW = "{\n  \"schema\": \"bcsp-new-device-migration-uncertainty-acceptance-v1\",\n  \"date_Asia_Shanghai\": \"2026-10-25\",\n  \"status\": \"MIGRATION_UNCERTAINTY_ACCEPTED_FOR_PENDING_REQUEST_CREATION_ONLY\",\n  \"user_message\": \"��ȷ���ܸò�ȷ���Ժ󣬽���������Ȩѵ��request������ȫ����Դ��ֵ��ʧ�ܼ�ͣ�ͽ�ֹ�Զ����Թ���\",\n  \"referenced_review\": {\n    \"path\": \"E:\\\\Codex\\\\2026-06-06\\\\mamba-ccf-c-1-high-resolution\\\\outputs\\\\cranial_bcsp_geov1_20261024\\\\resource_rebind_implementation_v1\\\\first_run_contract_resource_review_v1\\\\first_run_contract_resource_migration_review_v1.json\",\n    \"bytes\": 15295,\n    \"sha256\": \"9cb6af6512867f13b1b9acc176a73c2682ea17b155969d720f4e0fb7614f0c56\"\n  },\n  \"new_identity\": {\n    \"hostname\": \"shu-common-25721452-notebook-3x9rq5-0\",\n    \"uid\": 1000,\n    \"project\": \"/home/jovyan/adapointr_work/PoinTr\",\n    \"gpu_uuid\": \"GPU-4b19574a-832d-b4fe-e655-a57462954d6a\",\n    \"gpu_name\": \"NVIDIA GeForce RTX 4090 D\",\n    \"driver_version\": \"570.190\",\n    \"nvidia_smi_memory_total_MiB\": 24564,\n    \"python_realpath\": \"/opt/conda/envs/adapointr-mamba/bin/python3.10\",\n    \"python_version\": \"3.10.20\",\n    \"torch_version\": \"2.4.1+cu118\",\n    \"numpy_version\": \"2.2.6\",\n    \"timm_version\": \"1.0.27\",\n    \"memory_query_semantics\": \"SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.\"\n  },\n  \"accepted_remaining_uncertainty\": [\n    \"New GPU UUID and driver570.190 native CUDA execution has not been empirically validated\",\n    \"No full AdamW/ordinaryBN training memory or3900-step completion validation on this device\",\n    \"Failure may occur at zero or partial committed updates; retain evidence,stop,no automatic retry/resume/batch reduction/backend substitution\"\n  ],\n  \"new_gpu_execution_validated\": false,\n  \"historical_GPU_evidence_only\": true,\n  \"is_training_execution_authorization\": false,\n  \"authorizes_only_pending_request_creation\": true,\n  \"unchanged_static_config_sha256\": \"86dbbb7b216a932209abd446bdd28408ad5327433834336f2584b087c1b35647\",\n  \"unchanged_order_sha256\": \"6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d\"\n}\n".encode('utf-8')
USER_GRANT = '明确授权该完整 SHA256 对应的唯一一次训练执行'

START = time.monotonic()
created, created_dirs = [], []
phase = 'FROZEN_REQUEST'
tmux_attempted = False

def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def jraw(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')

def event(value):
    print(json.dumps(value, ensure_ascii=False, allow_nan=False), flush=True)

def budget():
    need(time.monotonic() - START < 110, 'controller time budget')

def parents(p):
    for a in reversed(p.parents):
        if os.path.lexists(a):
            need(stat.S_ISDIR(a.lstat().st_mode), 'invalid/link parent: ' + str(a))

def absent(p):
    parents(p)
    need(not os.path.lexists(p), 'existing execution path: ' + str(p))

def exact(r):
    budget()
    p = Path(r['path'])
    parents(p)
    st = p.lstat()
    need(stat.S_ISREG(st.st_mode) and st.st_size == r['bytes'], 'bound type/size: ' + str(p))
    raw = p.read_bytes()
    after = p.stat()
    need((st.st_ino, st.st_size, st.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns),
         'bound file changed: ' + str(p))
    need(sha(raw) == r['sha256'], 'bound hash: ' + str(p))
    return raw

def secure_dir(p):
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in p.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise

def create_dir(p):
    absent(p)
    fd = secure_dir(p.parent)
    try:
        os.mkdir(p.name, 0o700, dir_fd=fd)
        created_dirs.append(str(p))
    finally:
        os.close(fd)

def create_file(p, raw, mode=0o600):
    absent(p)
    fd = secure_dir(p.parent)
    try:
        child = os.open(p.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode, dir_fd=fd)
        created.append(str(p))
        with os.fdopen(child, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(fd)
    r = dict(path=str(p), bytes=len(raw), sha256=sha(raw))
    exact(r)
    return r

def cmd(args, timeout=10):
    r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return dict(returncode=r.returncode, stdout=r.stdout.decode('utf-8'), stderr=r.stderr.decode('utf-8'))

def tail(p, size=8192):
    if not p.is_file() or p.is_symlink():
        return ''
    with p.open('rb') as stream:
        stream.seek(max(0, p.stat().st_size-size))
        return stream.read(size).decode('utf-8', errors='replace')

try:
    need(sha(SCOPE_RAW) == SCOPE_SHA, 'authorized execution scope hash')
    scope = json.loads(SCOPE_RAW)
    q, accept = json.loads(Q_RAW), json.loads(ACCEPT_RAW)
    need(scope['status'] == q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION'
         and scope['execution_authorized'] is False, 'immutable pending requests')
    for key, raw in [('entry_request', Q_RAW), ('migration_acceptance', ACCEPT_RAW)]:
        need(len(raw) == scope[key]['bytes'] and sha(raw) == scope[key]['sha256'], key + ' binding')
    need(accept['authorizes_only_pending_request_creation'] is True
         and accept['is_training_execution_authorization'] is False
         and accept['new_gpu_execution_validated'] is False, 'migration acceptance boundaries')
    need(q['run_id'] == scope['run_id'] and q['fold'] == 'C' and q['n_input'] == 8192, 'single frozen run')
    paths = scope['future_paths']
    project = Path(q['identity']['project'])
    control = Path(paths['entry_request']).parent
    output = Path(paths['output'])
    identity = q['identity']
    phase = 'IDENTITY_RESOURCE_FRESHNESS'
    need(socket.gethostname() == identity['hostname'] and os.getuid() == identity['uid'], 'hostname/uid')
    parents(project)
    need(stat.S_ISDIR(project.lstat().st_mode), 'project directory')
    os.chdir(project)
    need(str(Path.cwd()) == str(project), 'cwd')
    py = Path(identity['python_realpath'])
    exact(dict(path=str(py), bytes=17331920,
               sha256='01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d'))
    version = cmd([str(py), '-I', '-S', '-B', '--version'], 5)
    need(version['returncode'] == 0 and (version['stdout']+version['stderr']).strip() == 'Python 3.10.20',
         'fixed Python version')
    gpu = cmd(['/usr/bin/nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used',
               '--format=csv,noheader,nounits'])
    need(gpu['returncode'] == 0 and len(gpu['stdout'].strip().splitlines()) == 1, 'one GPU query')
    v = [x.strip() for x in gpu['stdout'].strip().split(',')]
    need(v[:4] == [identity['gpu_uuid'], identity['gpu_name'], identity['driver_version'],
                   str(identity['nvidia_smi_memory_total_MiB'])] and int(v[4]) <= 256,
         'GPU identity/idle')
    processes = cmd(['/usr/bin/nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                     '--format=csv,noheader,nounits'])
    need(processes['returncode'] == 0 and not processes['stdout'].strip(), 'no other compute process')
    free = shutil.disk_usage(project).free
    need(free >= scope['resources_unchanged']['static']['minimum_free_disk_bytes'], 'disk reserve')
    absent(control)
    absent(output)
    for key in ('execution_scope', 'migration_acceptance', 'entry_request', 'authorization',
                'runtime', 'launcher', 'launch_attempt'):
        need(Path(paths[key]).parent == control, 'exact control parent')
        absent(Path(paths[key]))
    need(os.access(control.parent, os.W_OK | os.X_OK)
         and os.access(output.parent, os.W_OK | os.X_OK), 'owned parents writable')
    session = paths['tmux_session']
    session_probe = cmd(['/usr/bin/tmux', 'has-session', '-t', session], 5)
    need(session_probe['returncode'] == 1, 'unused tmux session')
    phase = 'FROZEN_IMPLEMENTATION_DATA_ASSETS'
    records = [q['static_config'], q['order_plan'], q['GPU_audit'], q['preflight_scope'],
               q['resource_rebind'], *q['implementation'].values(), q['QC']['qualified_receipt'],
               q['QC']['verification'], q['QC']['fold_binding'], *q['QC']['manifests'].values()]
    blobs = {r['path']: exact(r) for r in records}
    config = json.loads(blobs[q['static_config']['path']])
    need(config['resources'] == scope['resources_unchanged']['static']
         and config['counts'] == dict(cases=315, sources=63, batch=8, epochs=100,
                                      batches_per_epoch=39, updates=3900, exposures=31200),
         'frozen resource/count contract')
    rebind = json.loads(blobs[q['resource_rebind']['path']])
    need(rebind['new_identity'] == identity and rebind['new_gpu_execution_validated'] is False
         and rebind['historical_GPU_evidence_only'] is True, 'rebound metadata')
    rr = dict(rebind['new_readonly_report'])
    rr['path'] = str(Path(q['resource_rebind']['path']).parent / rr['path'])
    readonly_report = json.loads(exact(rr))
    assets_checked = []
    for r in readonly_report['frozen_assets']['manifest']:
        frozen = dict(path=r['path'], bytes=r['expected_bytes'], sha256=r['expected_sha256'])
        exact(frozen)
        assets_checked.append(frozen)
    need(len(assets_checked) == 30, 'exact selected assets')
    qualified = json.loads(blobs[q['QC']['qualified_receipt']['path']])
    need(qualified['verification'] == q['QC']['verification']
         and qualified['manifests'] == q['QC']['manifests']
         and qualified['fold_binding'] == q['QC']['fold_binding']
         and qualified['fold'] == 'C' and qualified['n_input'] == 8192,
         'qualified QC exact paths')
    folds = json.loads(blobs[q['QC']['fold_binding']['path']])['folds']['C']
    ids, sources = folds['train_case_ids'], folds['train_sources']
    need(len(ids) == len(set(ids)) == 315 and len(sources) == len(set(sources)) == 63
         and not set(sources) & set(folds['dev_sources']), 'fixed train sources')
    need(sha(('\n'.join(ids)+'\n').encode()) == qualified['train_allowlist_sha256'], 'train allowlist')
    manifest = {r['case_id']: r for r in
                (json.loads(line) for line in blobs[q['QC']['manifests']['8192']['path']].decode().splitlines())}
    need(len(manifest) == 420, 'manifest metadata count')
    counts = {source: 0 for source in sources}
    payload_bytes = 0
    data_root = Path(q['data_root'])
    for cid in ids:
        budget()
        r = manifest[cid]
        need(r['source_id'] in counts and r['n_input'] == r['n_target'] == 8192
             and r['normalization_source'] == 'defective_bbox', 'training data metadata')
        counts[r['source_id']] += 1
        p = data_root / r['point_path']
        need(data_root in p.parents and p.suffix == '.npz', 'explicit payload boundary')
        parents(p)
        st = p.lstat()
        need(stat.S_ISREG(st.st_mode) and 0 < st.st_size < 4194304, 'payload type/size: ' + str(p))
        exact(dict(path=str(p), bytes=st.st_size, sha256=r['sha256']))
        payload_bytes += st.st_size
    need(set(counts.values()) == {5} and payload_bytes == 49440750, 'fixed315 payload bytes/sources')
    plan = json.loads(blobs[q['order_plan']['path']])
    need(plan['case_ids'] == ids and len(plan['epochs']) == 100, 'authoritative order identity')
    for epoch, row in enumerate(plan['epochs']):
        batches = row['batches']
        flat = [x for batch in batches for x in batch] + row['dropped']
        need(row['epoch'] == epoch and len(batches) == 39 and all(len(b) == 8 for b in batches)
             and len(row['dropped']) == 3 and len(flat) == len(set(flat)) == 315
             and set(flat) == set(ids), 'shared order counts')
    # Last metadata freshness check immediately before any control write.
    absent(control)
    absent(output)
    need(cmd(['/usr/bin/tmux','has-session','-t',session],5)['returncode'] == 1, 'tmux became occupied')
    event(dict(status='TRAIN_PREWRITE_CHECKS_PASS', scope_sha256=SCOPE_SHA,
               hostname=socket.gethostname(), GPU_header=v, free_bytes=free,
               bound_records=len(records), selected_assets=30, train_payloads=315,
               payload_bytes=payload_bytes, server_writes_so_far=0))
    phase = 'MATERIALIZE_ONE_WAY'
    create_dir(control)
    materialized = []
    for key, raw in [('execution_scope', SCOPE_RAW), ('migration_acceptance', ACCEPT_RAW),
                     ('entry_request', Q_RAW)]:
        materialized.append(create_file(Path(paths[key]), raw))
    grant_text = ('用户原文：' + USER_GRANT + '\n授权上下文 execution_scope_sha256=' + SCOPE_SHA
                  + '\n入口 request_sha256=' + sha(Q_RAW))
    auth = dict(schema='bcsp-training-authorization-v1', request_sha256=sha(Q_RAW),
                explicit_user_authorization=True, user_authorization_text=grant_text)
    auth_raw = jraw(auth)
    auth_record = create_file(Path(paths['authorization']), auth_raw)
    materialized.append(auth_record)
    runtime = dict(schema='bcsp-training-runtime-v1', request_sha256=sha(Q_RAW),
                   authorization_sha256=auth_record['sha256'])
    runtime_raw = jraw(runtime)
    runtime_record = create_file(Path(paths['runtime']), runtime_raw)
    materialized.append(runtime_record)
    argv = scope['future_materialization_contract']['external_training_argv']
    argv = [auth_record['sha256'] if x == '<computed_authorization_SHA256>' else
            runtime_record['sha256'] if x == '<computed_runtime_SHA256>' else x for x in argv]
    need(argv[:4] == ['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s'], 'external timeout')
    lines = ['#!/usr/bin/env bash', 'set -u', 'set -o pipefail', 'set -o noclobber', 'umask 077',
             'cd ' + shlex.quote(str(project)) + ' || exit 65']
    for k, venv in scope['environment'].items():
        lines.append('export ' + k + '=' + shlex.quote(venv))
    for record in (materialized[2], auth_record, runtime_record):
        lines.append('[ "$(sha256sum -- ' + shlex.quote(record['path'])
                     + ' | cut -d \' \' -f 1)" = ' + shlex.quote(record['sha256']) + ' ] || exit 65')
    lines += ['mkdir -- ' + shlex.quote(str(output)) + ' || exit 73',
              '[ -d ' + shlex.quote(str(output)) + ' ] && [ ! -L '
              + shlex.quote(str(output)) + ' ] || exit 73',
              'set +e', shlex.join(argv) + ' > ' + shlex.quote(paths['log']) + ' 2>&1',
              'training_rc=$?', 'printf \'%s\\n\' "$training_rc" > ' + shlex.quote(paths['exit_code']),
              'save_rc=$?', '[ "$save_rc" -eq 0 ] || exit 74', 'exit "$training_rc"']
    launcher_raw = ('\n'.join(lines) + '\n').encode('utf-8')
    materialized.append(create_file(Path(paths['launcher']), launcher_raw, 0o700))
    phase = 'CLAIM_SINGLE_LAUNCH'
    absent(output)
    need(cmd(['/usr/bin/tmux','has-session','-t',session],5)['returncode'] == 1, 'tmux collision before claim')
    marker = dict(status='CLAIMED_BEFORE_TMUX', request_sha256=sha(Q_RAW),
                  execution_scope_sha256=SCOPE_SHA,
                  UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), automatic_retry=False)
    materialized.append(create_file(Path(paths['launch_attempt']), jraw(marker)))
    event(dict(status='TRAIN_MATERIALIZED_AND_ATTEMPT_CLAIMED', files=materialized,
               auth_content_base64=base64.b64encode(auth_raw).decode(),
               runtime_content_base64=base64.b64encode(runtime_raw).decode(),
               launcher_content_base64=base64.b64encode(launcher_raw).decode()))
    phase = 'TMUX_SINGLE_START'
    tmux_attempted = True
    launch = cmd(['/usr/bin/tmux','new-session','-d','-s',session,
                  'bash ' + shlex.quote(paths['launcher'])],10)
    need(launch['returncode'] == 0, 'tmux start nonzero: ' + launch['stderr'])
    phase = 'READONLY_STARTUP_CONFIRMATION'
    deadline = time.monotonic() + 30
    state = {}
    while time.monotonic() < deadline:
        budget()
        session_state = cmd(['/usr/bin/tmux','has-session','-t',session],5)
        pid_path = Path(paths['worker_pid'])
        pid = int(pid_path.read_text().strip()) if pid_path.is_file() and not pid_path.is_symlink() else None
        worker_live = False
        if pid is not None:
            proc = Path('/proc') / str(pid)
            if proc.exists():
                worker_live = (str(q['implementation']['entry']['path']).encode()
                               in (proc/'cmdline').read_bytes().split(b'\0'))
        exit_path = Path(paths['exit_code'])
        exit_code = int(exit_path.read_text().strip()) if exit_path.is_file() else None
        last_metric = None
        metric_tail = tail(Path(paths['metrics']))
        if metric_tail.strip():
            try:
                last_metric = json.loads(metric_tail.strip().splitlines()[-1])
            except (ValueError, IndexError):
                pass
        failure_present = any(Path(paths[key]).is_file() for key in ('failure','startup_failure'))
        state = dict(tmux_present=session_state['returncode']==0, worker_pid=pid, worker_live=worker_live,
                     exit_code=exit_code, last_committed_step=last_metric.get('step') if last_metric else None,
                     completion_present=Path(paths['completion']).is_file(), failure_present=failure_present)
        if exit_code is not None or failure_present or last_metric is not None:
            break
        if session_state['returncode'] != 0:
            time.sleep(0.2)
            break
        time.sleep(0.5)
    need(not state.get('failure_present') and state.get('exit_code') in (None, 0),
         'training startup failed: ' + repr(state))
    need((state.get('tmux_present') and state.get('worker_live')) or
         (state.get('exit_code') == 0 and state.get('completion_present')), 'startup not confirmed')
    event(dict(status='TRAINING_STARTED' if state.get('exit_code') is None else 'TRAINING_EXITED_AWAITING_AUDIT',
               state=state, scope_sha256=SCOPE_SHA, paths=paths,
               new_gpu_execution_validated=False, post_training_freeze_audit_performed=False,
               seconds=time.monotonic()-START, UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
except BaseException as exc:
    failure = dict(status='FAILED_STOP_NO_RETRY', phase=phase, error=repr(exc),
                   created_files=created, created_directories=created_dirs, tmux_attempted=tmux_attempted,
                   scope_sha256=SCOPE_SHA, no_retry=True, no_resume=True, no_cleanup=True)
    if 'paths' in globals():
        failure['launch_log_tail'] = tail(Path(paths['log']))
        failure['exit_code_text'] = tail(Path(paths['exit_code']),256)
        for key in ('failure','startup_failure'):
            failure[key] = tail(Path(paths[key]))
    event(failure)
    raise
