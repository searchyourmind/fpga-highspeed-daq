.PHONY: tools versions lint smoke fifo streaming models test e2e benchmark synthesis power pcb portfolio all
RUN = ./tools/run

tools:
	docker build -t fpga-daq-tools:1 -f tools/Dockerfile .
versions:
	$(RUN) bash tools/versions.sh
lint:
	$(RUN) python tools/lint.py
smoke:
	$(RUN) python tools/rtl_tests.py counter
fifo:
	$(RUN) python tools/rtl_tests.py fifo
streaming:
	$(RUN) python tools/rtl_tests.py streaming
models:
	$(RUN) python -m pytest -q tests --junitxml=results/models.xml
test:
	$(RUN) python -m pytest -q tests --junitxml=results/models.xml
	$(RUN) python tools/rtl_tests.py all
e2e:
	$(RUN) python tools/rtl_tests.py e2e
benchmark: e2e
	$(RUN) python tools/plot_benchmark.py
synthesis:
	$(RUN) python tools/synthesize.py
power:
	$(RUN) python hardware/power_tree/fetch_models.py
	$(RUN) python hardware/power_tree/analyze.py
	$(RUN) python hardware/power_tree/corners.py
	$(RUN) python tools/power_evidence.py
pcb:
	./tools/run-eda sh tools/pcb-build.sh
portfolio:
	./tools/run-eda python3 tools/release_pdf.py
verify: lint test synthesis
all:
	python3 tools/full_check.py

eda-tools:
	docker build -t fpga-daq-eda:2 -f tools/Dockerfile.kicad .

pcb-rebuild:
	./tools/run-eda sh tools/pcb-rebuild.sh
pcb-draft:
	./tools/run-eda sh tools/pcb-draft.sh
router-tools:
	docker build -t fpga-daq-router:1 -f tools/Dockerfile.router .

.PHONY: analysis-tools pcb-engineering pcb-engineering-check
analysis-tools:
	docker build -t fpga-daq-analysis:1 -f tools/Dockerfile.analysis .
pcb-engineering:
	python3 tools/pcb_engineering.py $(PCB_REVIEW_ARGS)
pcb-engineering-check:
	./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/check_evidence.py

.PHONY: extended timing
extended:
	$(RUN) python tools/rtl_tests.py extended
timing: synthesis
	$(RUN) python tools/timing_audit.py

.PHONY: pcb-views release-assets pcb-independent
pcb-views:
	./tools/run-eda sh tools/pcb-views.sh
release-assets:
	$(RUN) python tools/release_assets.py
pcb-independent:
	$(RUN) python hardware/reference_pcie_adapter/analysis/voltage_root_cause.py
	./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/thermal_independent_review.py
	./tools/run-analysis python3 hardware/reference_pcie_adapter/analysis/si_independent_review.py
	python3 tools/write_independent_review.py
