PY ?= .venv/bin/python

.PHONY: test lint smoke dataset benchmark suite shared-suite render-install render play demo human-bc fault-benchmark fault-recovery fault-power power-benchmark power-allocation power-allocation-stochastic perf

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check src tests
	$(PY) -m mypy src

smoke:
	$(PY) -m fabline smoke --ticks 200

dataset:
	$(PY) -m fabline dataset --episodes 100 --out datasets/factory-debug-v0.1

benchmark:
	$(PY) -m fabline benchmark --dataset datasets/factory-debug-v0.1 --out results/m1-benchmark

suite:
	$(PY) -m fabline suite --out results/m2-suite --episodes 50

shared-suite:
	$(PY) -m fabline shared-suite --out results/factory-v0.1

render-install:
	.tools/uv pip install --python .venv/bin/python -e ".[render]"

render:
	$(PY) -m fabline render --config configs/factory_shared.toml

play:
	$(PY) -m fabline play --out datasets/human-control-v0.1

demo:
	$(PY) -m fabline demo --episodes 10 --out datasets/demo-control-v0.1

human-bc:
	$(PY) -m fabline human-bc --dataset datasets/demo-control-v0.1 --out results/human-bc

fault-benchmark:
	$(PY) -m fabline fault-benchmark --out results/fault-benchmark

fault-recovery:
	$(PY) -m fabline fault-recovery --out results/fault-recovery

fault-power:
	$(PY) -m fabline fault-power --out results/fault-power --episodes 5 --train-episodes 200 --capacity 5 --threshold 5 --repair-ticks 30 --success-score 90

power-benchmark:
	$(PY) -m fabline power-benchmark --out results/power-benchmark

power-allocation:
	$(PY) -m fabline power-allocation --out results/power-allocation

wire-repair:
	$(PY) -m fabline wire-repair --out results/wire-repair --episodes 5 --train-episodes 300 --seeds 200,201,202,203,204 --train-seed-start 5000 --repair-ticks 60 --repair-cost 1.0

wire-maintenance:
	$(PY) -m fabline wire-maintenance --out results/wire-maintenance --episodes 5 --train-episodes 200 --seeds 300,301,302,303,304 --train-seed-start 6000

preventive-fault:
	$(PY) -m fabline preventive-fault --out results/preventive-fault --episodes 5 --train-episodes 500 --seeds 400,401,402,403,404 --train-seed-start 7000

preventive-threshold:
	$(PY) -m fabline preventive-threshold --out results/preventive-threshold --train-episodes 50 --seeds 700,701,702,703,704 --train-seed-start 9000

crew-schedule:
	$(PY) -m fabline crew-schedule --out results/crew-schedule --episodes 5 --train-episodes 500 --seeds 800,801,802,803,804 --train-seed-start 15000

multi-crew:
	$(PY) -m fabline multi-crew --out results/multi-crew --episodes 5 --train-episodes 500 --seeds 1000,1001,1002,1004,1005 --train-seed-start 30000

crew-robustness:
	$(PY) -m fabline crew-robustness --out results/crew-robustness --seeds 3000,3001,3002,3003,3004,3005,3006,3007,3008,3009,3010,3011,3012,3013,3014,3015,3016,3017,3018,3019,3020,3021,3022,3023,3024,3025,3026,3027,3028,3029,3030,3031,3032,3033,3034,3035,3036,3037,3038,3039 --q-seeds 0,1,2,3,4 --train-episodes 500 --train-seed-start 40000

crew-replan:
	$(PY) -m fabline crew-replan --out results/crew-replan --seeds 5000,5001,5002,5003,5004,5005,5006,5007,5008,5009 --q-seeds 0,1,2,3,4 --train-episodes 1000 --train-seed-start 45000

crew-layouts:
	$(PY) -m fabline crew-layouts --out results/crew-layouts --seeds 6000,6001,6002,6003,6004,6005,6006,6007,6008,6009 --train-episodes 500 --train-seed-start 55000

power-allocation-stochastic:
	$(PY) -m fabline power-allocation --out results/power-allocation/stochastic --episodes 5 --train-episodes 100 --load-jitter 30 --capacity-jitter 20 --variation-period 20

perf:
	FABLINE_PERF=1 $(PY) -m pytest tests/perf -q
