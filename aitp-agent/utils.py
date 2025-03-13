class Utils(object):
  def __init__(self):
    pass

  def is_code_block(self, code):
    return code.startswith("```") and code.endswith("```")

  def is_all_required_params_filled(self, data, required_params):
    return all(param in data and bool(data[param]) for param in required_params)

  def remove_null_values(self, obj):
    if isinstance(obj, dict):
        return {k: self.remove_null_values(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [self.remove_null_values(i) for i in obj if i is not None]
    return obj