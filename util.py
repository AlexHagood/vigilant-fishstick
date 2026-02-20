def float_to_wear(float_value: float) -> str:
    if float_value < 0.07:
        return "Factory New"
    elif float_value < 0.15:
        return "Minimal Wear"
    elif float_value < 0.38:
        return "Field-Tested"
    elif float_value < 0.45:
        return "Well-Worn"
    else:
        return "Battle-Scarred"