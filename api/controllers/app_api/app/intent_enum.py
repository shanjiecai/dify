# 列举所有intent类型
# 目前有
# 1、无明确意图
# 2、提取出目标或知识点，需要模型问问题生成详细计划，judge_plan
# 3、用户强制需要生成计划，直接调用计划接口，judge_force_plan


# python枚举

from enum import Enum


class Intent(Enum):
    NONE = None
    JUDGE_PLAN = "judge_plan"
    JUDGE_FORCE_PLAN = "judge_force_plan"

