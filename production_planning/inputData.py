import gurobipy as gp
import productionPlan, productionPlan_with_promotion

# Demand Data
# Months in integer for calculations
months, monthly_demand_forecast = gp.multidict({
    1: 47000,
    2: 49000,
    3: 52000,
    4: 35000,
    5: 31000,
    6: 22000,
    7: 26000,
    8: 34000,
    9: 39000,
    10: 41000,
    11: 45000,
    12: 46000
})

# Work and Employee Data
monthy_working_days = 25 # days per month
working_hours_per_working_day = 9 # hours per day
standard_hourly_wage = 16 # euros
overtime_hourly_wage = 18 # euros
max_overtime_hours_per_month = 16 # maximum limit of overtime hours per month
current_num_employees = 200 # current number of employees in production

employee_hiring_cost = 850 # euros
employee_layoff_cost = 1400 # euros
max_employees_to_hire_per_month = 100 # maximum number of employees that can be hired per month

# Production Data
production_time_per_unit = 2.5 # hours per unit
holding_cost_per_unit_per_month = 10 # euros per unit
inventory_storage_limit = 25000 # units that can be stored

# Costs of Production
raw_material_cost_per_unit = 25 # euros
selling_price_per_unit = 80 # euros
third_party_production_cost_per_unit = 72 # euros
initial_inventory_level = 2800 # units available in stock
penalty_cost_per_delayed_unit = 13 # euros


productionPlan.solve(
    months=months,
    monthly_demand_forecast=monthly_demand_forecast,
    monthy_working_days=monthy_working_days,
    working_hours_per_working_day=working_hours_per_working_day,
    standard_hourly_wage=standard_hourly_wage,
    overtime_hourly_wage=overtime_hourly_wage,
    max_overtime_hours_per_month=max_overtime_hours_per_month,
    current_num_employees=current_num_employees,
    employee_hiring_cost=employee_hiring_cost,
    employee_layoff_cost=employee_layoff_cost,
    max_employees_to_hire=max_employees_to_hire_per_month,
    production_time_per_unit=production_time_per_unit,
    holding_cost_per_unit_per_month=holding_cost_per_unit_per_month,
    inventory_storage_limit=inventory_storage_limit,
    raw_material_cost_per_unit=raw_material_cost_per_unit,
    selling_price_per_unit=selling_price_per_unit,
    third_party_production_cost_per_unit=third_party_production_cost_per_unit,
    initial_inventory_level=initial_inventory_level,
    penalty_cost_per_unit=penalty_cost_per_delayed_unit,
)

productionPlan_with_promotion.solve(
    months=months,
    monthly_demand_forecast=monthly_demand_forecast,
    monthy_working_days=monthy_working_days,
    working_hours_per_working_day=working_hours_per_working_day,
    standard_hourly_wage=standard_hourly_wage,
    overtime_hourly_wage=overtime_hourly_wage,
    max_overtime_hours_per_month=max_overtime_hours_per_month,
    current_num_employees=current_num_employees,
    employee_hiring_cost=employee_hiring_cost,
    employee_layoff_cost=employee_layoff_cost,
    max_employees_to_hire=max_employees_to_hire_per_month,
    production_time_per_unit=production_time_per_unit,
    holding_cost_per_unit_per_month=holding_cost_per_unit_per_month,
    inventory_storage_limit=inventory_storage_limit,
    raw_material_cost_per_unit=raw_material_cost_per_unit,
    selling_price_per_unit=selling_price_per_unit,
    third_party_production_cost_per_unit=third_party_production_cost_per_unit,
    initial_inventory_level=initial_inventory_level,
    penalty_cost_per_unit=penalty_cost_per_delayed_unit,
)
