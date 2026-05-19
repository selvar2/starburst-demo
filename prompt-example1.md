Update mcp2ohio.test_writes.scratch_nl_table set label = 'regional_chart_ready' where id = 101

In catalog mcp2ohio, schema test_writes, add a row to table executive_kpis_nl with kpi_name Annual Recurring Revenue, current_value 184500000, target_value 172000000, trend_direction up

Add a new row into catalog mcp2ohio, schema test_writes, table scratch_nl_table with id 101, label regional_chart_demo

--------------------------

INSERT INTO mcp2ohio.test_writes.scratch_nl_table (id, label)
VALUES (101, 'regional_chart_demo')

INSERT INTO mcp2ohio.test_writes.customer_metrics_nl (customer_id, customer_name, revenue, growth_percent)
VALUES (9001, 'Acme Enterprise', 125000.50, 0.18)

INSERT INTO mcp2ohio.test_writes.executive_kpis_nl (kpi_name, current_value, target_value, trend_direction)
VALUES ('Annual Recurring Revenue', 184500000, 172000000, 'up')

UPDATE mcp2ohio.test_writes.scratch_nl_table
SET label = 'regional_chart_1'
WHERE id = 101

----------------

CREATE SCHEMA mcp2ohio.zsandbox_schema1;

CREATE TABLE mcp2ohio.test_writes.zscratch_nl_table4 ( id INTEGER, label VARCHAR );
