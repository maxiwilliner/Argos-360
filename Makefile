.PHONY: install generate-data mdm dbt-snapshot dbt-run dbt-test pipeline dashboard lint clean

install:
	pip install -r requirements.txt

generate-data:
	python src/generator/generate_raw_data.py

mdm:
	python src/mdm/entity_resolution.py

dbt-snapshot:
	cd dbt_ecommerce && dbt snapshot --profiles-dir .

dbt-run:
	cd dbt_ecommerce && dbt run --profiles-dir .

dbt-test:
	cd dbt_ecommerce && dbt test --profiles-dir .

pipeline: generate-data mdm dbt-snapshot dbt-run dbt-test
	@echo "================================================="
	@echo " [SUCCESS] ARGOS-360 Pipeline executed cleanly!"
	@echo "================================================="

dashboard:
	streamlit run app/dashboard.py

lint:
	sqlfluff lint dbt_ecommerce/models/

clean:
	rm -rf data/01_raw/*.parquet data/02_silver/*.parquet data/03_gold/*.parquet *.duckdb
