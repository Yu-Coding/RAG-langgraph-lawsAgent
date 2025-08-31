class MCPPlanner:
    def __init__(self):
        self.state = {
            "landlord": None,
            "tenant": None,
            "location": None,
            "rent": None,
            "duration": None,
        }
        self.current_field = None  # ✅ 记录当前正在填写哪个字段
        
        self.chinese_labels = {
            "landlord": "房东",
            "tenant": "租客",
            "location": "地址",
            "rent": "租金",
            "duration": "租期",
        }
        
        self.finished_contract_text = None  # 合同文本
        self.contract_ready = False         # ✅ 这里加上这一行
        self.contract_todo = False          # Going to do the contract

    def reset(self):
        self.state = {
            "landlord": None,
            "tenant": None,
            "location": None,
            "rent": None,
            "duration": None,
    }
    
    def is_complete(self):
        return all(self.state.values())

    def update(self, user_input: str):
        user_input = user_input.strip()
        
        
        # ✅ 如果当前有在问的字段，直接写进去
        if self.current_field:
            self.state[self.current_field] = user_input
            self.current_field = None
            return
        
        if "房东" in user_input or "出租人" in user_input:
            self.state["landlord"] = user_input
        elif "租客" in user_input or "承租人" in user_input:
            self.state["tenant"] = user_input
        elif "地址" in user_input or "位置" in user_input:
            self.state["location"] = user_input
        elif "租金" in user_input or "金额" in user_input:
            self.state["rent"] = user_input
        elif "租期" in user_input or "年" in user_input or "月" in user_input:
            self.state["duration"] = user_input

    def prompt_next(self):
        for key, value in self.state.items():
            if value is None:
                self.current_field = key  # ✅ 标记接下来要填哪个字段
                return f"请告诉我{self.chinese_labels[key]}是什么？"
        return None

    def build_contract_request(self):
        self.finished_contract_text = f"""【租赁合同草案】
- 房东: {self.state['landlord']}
- 租客: {self.state['tenant']}
- 地址: {self.state['location']}
- 租金: {self.state['rent']}
- 租期: {self.state['duration']}
请参考中华人民共和国民法典相关租赁规定，规范用词。
"""
        #self.contract_ready = True
        
        return self.finished_contract_text

planner = MCPPlanner()

