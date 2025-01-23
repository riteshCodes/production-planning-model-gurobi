import gurobipy as gp
from gurobipy import GRB, quicksum
from typing import Dict

def solve(
    months: list[int], # list of demand periods as int
    monthly_demand_forecast:  Dict[int, int], # key: demand period, value: demand forecasted
    monthy_working_days: int,
    working_hours_per_working_day: float,
    standard_hourly_wage: float,
    overtime_hourly_wage: float,
    max_overtime_hours_per_month: float,
    current_num_employees: int,
    employee_hiring_cost: float,
    employee_layoff_cost: float,
    max_employees_to_hire: int,
    production_time_per_unit: float,
    holding_cost_per_unit_per_month: float,
    inventory_storage_limit: int,
    raw_material_cost_per_unit: float,
    selling_price_per_unit: float,
    third_party_production_cost_per_unit: float,
    penalty_cost_per_unit: float,
    initial_inventory_level: int
):
    # Model for optimization
    model = gp.Model('Production-Planning')
    model.setParam("MIPGap", 1e-10)

    # DECISION VARIABLES:

    # Units produced in-house each month
    inhouse_production = model.addVars(months, name="In_House_Production", vtype=GRB.INTEGER)

    # Units produced by subcontracting third party each month
    third_party_production = model.addVars(months, name="Third_Party_Production", vtype=GRB.INTEGER)

    # Inventory at the end of each month, with month = 0 (initial inventory level)
    inventory = model.addVars([0] + months, name="Inventory", vtype=GRB.INTEGER)

    # Demands unfulfilled demand (stockout) at the end of each month, with month = 0 (initial stockout)
    stockout = model.addVars([0] + months, name="Stockout", vtype=GRB.INTEGER)

    # Total number of workers in each month, (m = 0 -> initial period, before beginning of production plan)
    number_of_employees = model.addVars([0] + months, name="Employees", vtype=GRB.INTEGER)

    # Total overtime each month for all employees
    overtime_hours = model.addVars(months, name="Overtime_Hours", vtype=GRB.INTEGER)

    # Employees hired each month to fulfill the demand
    hires = model.addVars(months, name="Hires", vtype=GRB.INTEGER)

    # Employees layed off each month to maintain the number of employees needed to fulfill the demand
    layoffs = model.addVars(months, name="Layoffs", vtype=GRB.INTEGER)

    # Promotion period, promotion_m == 1 iff the promotion is given at month m
    promotion = model.addVars(months, name="Promotion", vtype=GRB.BINARY)


    # PARAMETERS:

    # Working time
    total_regular_working_hours_per_month = (working_hours_per_working_day * monthy_working_days)

    # Total costs incurred
    total_revenue = quicksum(selling_price_per_unit * monthly_demand_forecast[m] for m in months)
    regular_work_time_wage_per_month = total_regular_working_hours_per_month * standard_hourly_wage
    regular_time_wage_costs = quicksum(number_of_employees[m] * regular_work_time_wage_per_month for m in months)
    overtime_wage_costs = quicksum(overtime_hours[m] * overtime_hourly_wage for m in months)
    cost_of_hiring = quicksum(hires[m] * employee_hiring_cost for m in months)
    cost_of_laying_off = quicksum(layoffs[m] * employee_layoff_cost for m in months)
    inhouse_production_cost = quicksum(raw_material_cost_per_unit * inhouse_production[m] for m in months)
    third_party_production_cost = quicksum(third_party_production_cost_per_unit * third_party_production[m] for m in months)
    inventory_holding_cost = quicksum(holding_cost_per_unit_per_month* inventory[m] for m in months)
    stockout_cost = quicksum(stockout[m] * penalty_cost_per_unit for m in months)

    # Promotion related
    max_number_of_promotion_months = 1
    promotion_price_per_unit = 1 # 1 monetary unit off the total retail price per unit
    demand_increase_rate = 10 # rate (percentage) at which the demand increases in the promotion period
    forward_buying_rate = 20 # forward buying rate (in demand) in each of the following two months after the promotion period

    total_demand_increase_via_promotion = quicksum(promotion[m] * (monthly_demand_forecast[m] * (demand_increase_rate / 100)) for m in months)
    total_forward_buying_via_promotion = quicksum(promotion[m] * ((monthly_demand_forecast[m + 1] * (forward_buying_rate / 100))
                                                            + (monthly_demand_forecast[m + 2] * (forward_buying_rate / 100)))
                                                            for m in months[:-2])
    price_cut_via_promotion = promotion_price_per_unit * quicksum(promotion[m] * monthly_demand_forecast[m] for m in months)
    price_gained_via_promotion = (selling_price_per_unit - promotion_price_per_unit) * total_demand_increase_via_promotion # total margin gained via increase in demand
    price_cut_via_forward_buying = promotion_price_per_unit * total_forward_buying_via_promotion

    # INITIAL CONSTRAINTS: 
    model.addConstr(inventory[0] == initial_inventory_level, name=f"Initial_Inventory_Level")
    model.addConstr(stockout[0] == 0, name=f"Stockout_Before_Planning")
    model.addConstr(number_of_employees[0] == current_num_employees, name=f"Initial_Number_Of_Employees")
    model.addConstr(stockout[months[-1]] == 0, name=f"Stockout_At_End") # No stockout at the end of the month

    # ADDITIONAL CONSTRAINTS:
    for m in months:
        
        # Workforce Balance Constraint: Number of workers per month
        model.addConstr(number_of_employees[m] == number_of_employees[m - 1] + hires[m] - layoffs[m],
                      name=f"WorkforceBalance_{m}")
    
        # Overtime Limit Constraint: Each employee must not exceed the overtime working hours limit given per month
        model.addConstr(overtime_hours[m] <= max_overtime_hours_per_month * number_of_employees[m], 
                        name=f"OvertimeLimit_{m}")
        
        # Hiring Limit Constraint: Total number of new hires each month should not exceed the maximum limit
        model.addConstr(hires[m] <= max_employees_to_hire, name=f"HiringLimit_{m}")

        # Inventory Space Limit Constraint: Inventory can not exceed the given storage capacity
        model.addConstr(inventory[m] <= inventory_storage_limit, name=f"InventorySpace_{m}")

        # Production Capacity Constraint: Production quantity can not exceed the available working and overtime hours
        model.addConstr(inhouse_production[m] <= 
                        (total_regular_working_hours_per_month / production_time_per_unit) * number_of_employees[m]
                        + (overtime_hours[m] / production_time_per_unit),
                        name=f"ProductionCapacity_{m}")
            
        # Inventory Balance Constraint (WITH PROMOTION):
        # Previous Inventory Level + Production + Subcontracting = Current Demand + Stockouts
        model.addConstr(
            inventory[m - 1] + # previous inventory
            inhouse_production[m] + third_party_production[m] # current total production
            ==
            inventory[m] # current inventory
            + stockout[m-1] # previous stockout
            + stockout[m] # current stockout
            + monthly_demand_forecast[m] # current demand
            + (promotion[m] * (forward_buying_rate / 100) * quicksum(monthly_demand_forecast[m_] for m_ in range(m + 1, m + 2 + 1) if m_ <= len(months)))
            + (promotion[m] * monthly_demand_forecast[m] * (demand_increase_rate / 100))
            - ((forward_buying_rate / 100) * monthly_demand_forecast[m] * quicksum(promotion[m_] for m_ in range(m - 2, m) if m_ > 0)),
            name=f"DemandBalance_{m}"
        )
    
    # PROMOTION CONSTRAINT
    model.addConstr(quicksum(promotion[m] for m in months) <= max_number_of_promotion_months, name="maximum_promotion_period") # maximum promotion periods
    model.addConstr(promotion[months[-1]] + promotion[months[-2]] == 0, name="no_promotion_in_last_two_months") # no promotion in the last two months of planning period


    # OBJECTIVE: Maximize total profit
    # Profit = Total Revenue - Cost of regular wage - Cost of working overtime 
    #          - Cost of hiring extra employees - Cost of laying off employees
    #          - Cost of holding unsold units - Cost of stockouts
    #          - Cost of inhouse production - Cost of subcontracting
    model.setObjective(
        total_revenue - regular_time_wage_costs - overtime_wage_costs 
        - cost_of_hiring - cost_of_laying_off
        - inventory_holding_cost - stockout_cost
        - inhouse_production_cost - third_party_production_cost
        - price_cut_via_forward_buying - price_cut_via_promotion + price_gained_via_promotion,
        sense=GRB.MAXIMIZE)

    # Update and solve the model
    model.update()
    model.optimize()

    # Results:
    if model.status == GRB.OPTIMAL:
        with open("output_production_plan.txt", "w") as file:
            print(f"----------------Optimal Profit Found: {model.ObjVal} Euros ----------------\n", file=file)
            for m in months:
                print(
                    "----------------------------------------------------------------------\n",
                    f"At the End of {m}.Month: \n",
                    f"Total Demand (Beginning of the Month): {monthly_demand_forecast[m]} units \n",
                    f"In-House Production: {inhouse_production[m].x} units \n", 
                    f"Third Party Production: {third_party_production[m].x} units \n",
                    f"Initial Inventory Level: {inventory[m - 1].x} units \n",
                    f"Final Inventory Level: {inventory[m].x} units \n", 
                    f"Unfulfilled Demand (Stockout): {stockout[m].x} units\n",
                    f"Total Employees: {number_of_employees[m].x}, from which \n ",
                    f"\t Total New Employees Hired: {hires[m].x} \n" ,
                    f"\t Total Existing Employees Layoff: {layoffs[m].x} \n",
                    f"\t Total Overtime Working Hours: {overtime_hours[m].x} \n" ,
                    file=file
                )
    else:
        print("No Optimal Solution Found.")