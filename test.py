import numpy as np
import gurobipy as gp
from gurobipy import GRB, quicksum

# 时间段数
T = 24 * 60 

# 机组数量
N = 6

# 参数
SUM_volume = 25000  # 总需运量

# 最小流量约束
flow_rate_min_m3h = 1000

# 最小流量约束
flow_rate_max_m3h = 2000

# 每个机组的流量 m3/h
flow_rate = np.array([1055, 1113, 1735, 1880, 1832, 2302])

# 每个机组的电功率 kW
power_rate = np.array([1102, 1120, 2222, 2352, 2370, 3472])

# 分时电价 ¥/kWh
electricity_price = np.array([0.211267, 0.211267, 0.211267, 0.211267, 0.211267, 0.211267, 0.211267, 0.211267,
                              0.552604, 0.552604, 
                              0.937986, 0.937986, 0.937986, 0.937986, 
                              0.552604, 0.552604, 0.552604, 0.552604, 0.552604, 
                              0.937986, 0.937986, 0.937986, 0.937986, 0.937986])

electricity_price_actual = np.zeros(T)
for i in range(T):
    electricity_price_actual[i] = electricity_price[i // 60]

# 每个班次的最大切换次数
max_switches_per_shift = 2

# 优化模型
model = gp.Model("test_model")

# 决策量
# 0/1决策矩阵 行为时刻数量，列为机组数量
X = model.addVars(T, N , vtype=GRB.BINARY, name="X")

# 显示机组状态是否切换的0/1变量，1表示切换，0表示不切换
#S = model.addVars(T, vtype=GRB.BINARY, name="S")

# 分段成本
opex_cost = model.addVars(T, vtype=GRB.CONTINUOUS, lb=0, name="opex_cost")

# 总成本
Total_cost = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="Total_cost")

# 约束条件
# 同一个时刻，运行一个机组
model.addConstrs((quicksum(X[t, j] for j in range(N)) == 1 for t in range(T)), name="one_unit_per_time")

# 总运量约束
model.addConstr(quicksum(X[t, j] * flow_rate[j] for t in range(T) for j in range(N)) / 60 >= SUM_volume, name="volume_def")
#model.addConstr(quicksum(X[t, j] * flow_rate[j] for t in range(T) for j in range(N)) <= SUM_volume + 1000, name="volume_def")

# 瞬时流量约束
model.addConstrs((quicksum(X[t, j] * flow_rate[j] for j in range(N)) >= flow_rate_min_m3h for t in range(T)), name="flow_rate_min_def")
model.addConstrs((quicksum(X[t, j] * flow_rate[j] for j in range(N)) <= flow_rate_max_m3h for t in range(T)), name="flow_rate_max_def")

# 切换次数约束
#model.addConstr(S[0] == 1, name="switch_def") # 初始时刻视为切换
# model.addConstr(quicksum(S[t] for t in range(0, 9)) <= max_switches_per_shift, name="max_switches_per_shift_def")
# model.addConstr(quicksum(S[t] for t in range(9, 21)) <= max_switches_per_shift, name="max_switches_per_shift_def")
# model.addConstr(quicksum(S[t] for t in range(21, 24)) <= max_switches_per_shift, name="max_switches_per_shift_def")

# 
#model.addConstrs((S[t] >= X[t, j] - X[t-1, j] for t in range(1, T) for j in range(N)), name="switch_logic_def")
#model.addConstrs((S[t] >= X[t-1, j] - X[t, j] for t in range(1, T) for j in range(N)), name="switch_logic_def")

#model.addConstrs((S[0] == 1 for j in range(N)), name="switch_logic_def")
#model.addConstrs((S[0] >= X[T-1, j] - X[0, j] for j in range(N)), name="switch_logic_def")

# 分段成本计算
model.addConstrs((opex_cost[t] == electricity_price_actual[t] / 60 * quicksum(X[t, j] * power_rate[j] for j in range(N)) for t in range(T)), name="opex_cost_def")

# 总成本计算
model.addConstr(Total_cost == quicksum(opex_cost[t] for t in range(T)), name="Total_cost_def")

# 目标函数
model.setObjective(Total_cost, GRB.MINIMIZE)

model.update()

# 求解
model.optimize()

#S_result =[S[t].X for t in range(T)]

X_result = np.array([[X[t, j].X for j in range(N)] for t in range(T)])

# 保存 X_result 到 CSV 文件
np.savetxt("X_result.csv", X_result, delimiter=",", fmt="%d")


