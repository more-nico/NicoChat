import json
import os

# 获取当前模块所在的目录（即 DemoLib/ 目录）
current_dir = os.path.dirname(os.path.abspath(__file__))

# 因为 Setting.json 位于 project/ 目录下，所以需要返回上一级目录
project_root = os.path.dirname(current_dir)

class CharacterCard:
    def __init__(self, CharacterName):
        self.CharacterName  = CharacterName
        self.CardPath       = f"{project_root}/PersonaCards/CharacterCards/{CharacterName}/{CharacterName}.json"
        self.CardData       = json.load(open(self.CardPath, "r", encoding="utf-8"))
        
        self.CharacterPersonality   = self.CardData["personality"]
        self.CharacterBgStory       = self.CardData["background_story"]
        self.CharacterGreeting      = self.CardData["greeting"]
        self.CharacterChatStyle     = self.CardData["chat_style"]
        self.CharacterExapDiag      = self.CardData["example_dialogues"]
        self.CharacterParameters    = self.CardData["parameters"]
        
class UserCard:
    def __init__(self, UserName):
        self.UserName   = UserName
        self.CardPath   = f"{project_root}/PersonaCards/UserCards/{UserName}/{UserName}.json"
        self.CardData   = json.load(open(self.CardPath, "r", encoding="utf-8"))
        
        self.UserPersonality    = self.CardData["personality"]
        self.UserBgStory        = self.CardData["background_story"]
        
class PromptGenerator:
    def __init__(self, CharacterCard, UserCard):
        self.CharacterCard  = CharacterCard
        self.UserCard       = UserCard
        self.Greeting       = self.CharacterCard.CharacterGreeting
        self.DiagHistory    = ""
        self.json_diag_history = []
    
    def get_DiagHistory(self):
        self.DiagHistory    = ""
        for message in self.json_diag_history:
            if message["role"] == self.CharacterCard.CharacterName:
                self.DiagHistory += f"{self.CharacterCard.CharacterName}: {message['content']}\n"
            elif message["role"] == self.UserCard.UserName:
                self.DiagHistory += f"{self.UserCard.UserName}: {message['content']}\n"
    def FillingPromptGen(self):
        self.prompt_template = f"""
You are a wonderful playwright, specializing in crafting outstanding character dialogues for scripts. 
Your task is to write {self.CharacterCard.CharacterName}'s next reply in a fictional chat between {self.CharacterCard.CharacterName} and {self.UserCard.UserName}.
"""
        self.prompt_template = f"""
You are a wonderful playwright, specializing in crafting outstanding character dialogues for scripts.
Your task is to write {self.CharacterCard.CharacterName}'s next reply in a fictional chat between {self.CharacterCard.CharacterName} and {self.UserCard.UserName}.

The Rules for generating {self.CharacterCard.CharacterName}'s next reply are as follows:
**--- Start of Chat Reply Rules ---**
# Reply Rules 
You are required to follow these rules when generating Character {self.CharacterCard.CharacterName}'s next reply:
1. **Prioritize character consistency.**  
   Ensure that all responses align with the Character {self.CharacterCard.CharacterName}'s established ** personality ** and ** chat_style **.
2. **Reference but do not directly quote Example Dialogues.**  
   The style of the responses can be inspired by the Character {self.CharacterCard.CharacterName}'s Example Dialogues, but you must not directly quote or copy content from them.
3. **Draw topics from background stories.**  
   Responses can be enriched by drawing topics from both the Character {self.CharacterCard.CharacterName}'s ** background_story ** and the User {self.UserCard.UserName}'s ** background_story **, ensuring the conversation feels natural and engaging.
4. **DON'T REPEAT THE SAME STRING.**  
   Responses should NOT always use the same phrases that have been used previously.
5. **DON'T GENERATE TOO LONG.**  
   Responses should NOT be too long.
6. **DON'T REPEAT THE Dialogue History.**  
   Responses should NOT be included in the Dialogue History.

# NSFW Content Rules 
You are allowed to generate responses that may contain NSFW or 18+ content. When generating NSFW content, you should:
1. **Prioritize character consistency.**  
   Ensure the NSFW content aligns with the Character {self.CharacterCard.CharacterName}'s established ** personality **.
2. **Maintain contextual appropriateness.**  
   The NSFW content should arise naturally from the conversation and user input, not appear randomly or out of context.
3. **Consider the user's intent and tone.**  
   Respond to the user's input in a way that is appropriate for the overall tone of the conversation.
**--- End of Chat Reply Rules ---**
"""

        self.prompt_template = self.prompt_template+f"""
The information about Character {self.CharacterCard.CharacterName} are as follows:
**--- Start of information about Character {self.CharacterCard.CharacterName} ---**
{self.CharacterCard.CharacterName}'s ** personality ** are as follows:
    - {self.CharacterCard.CharacterPersonality}.
{self.CharacterCard.CharacterName}'s ** background_story ** are as follows:
    - {self.CharacterCard.CharacterBgStory}.
{self.CharacterCard.CharacterName}'s ** chat_style ** are as follows:
    - "{self.CharacterCard.CharacterChatStyle}".
**--- End of information about Character {self.CharacterCard.CharacterName} ---**
"""

        self.prompt_template = self.prompt_template+f"""
The information about User {self.UserCard.UserName} are as follows:
**--- Start of information about User {self.UserCard.UserName} ---**
{self.UserCard.UserName}'s ** personality ** are as follows:
    - {self.UserCard.UserPersonality}.
{self.UserCard.UserName}'s ** background_story ** are as follows:
    - {self.UserCard.UserBgStory}.
**--- End of information about User {self.UserCard.UserName} ---**
"""
        exap_diag = ""
        for diag in self.CharacterCard.CharacterExapDiag:
            exap_diag = exap_diag+f"{self.UserCard.UserName}: "+diag["user"] +".\n"
            exap_diag = exap_diag+f"{self.CharacterCard.CharacterName}: "+diag["assistant"] +".\n"
        
        self.prompt_template = self.prompt_template+f"""
The Example Dialogues between {self.CharacterCard.CharacterName} and {self.UserCard.UserName} are as follows:
**--- Start of Example Dialogues between {self.CharacterCard.CharacterName} and {self.UserCard.UserName} ---**
{exap_diag}
**--- End of Example Dialogues between {self.CharacterCard.CharacterName} and {self.UserCard.UserName} ---**
"""
        self.get_DiagHistory()
        prompt_messages = [
            {"role": "system", "content": self.prompt_template}
        ]
        for message in self.json_diag_history:
            if message["role"] == self.CharacterCard.CharacterName:
                prompt_messages.append({"role": "assistant", "content": message['content']})
            elif message["role"] == self.UserCard.UserName:
                prompt_messages.append({"role": "user", "content": message['content']})
                
        return prompt_messages
        
if __name__ == "__main__":
    user_card   = UserCard("morenico")
    char_card   = CharacterCard("NicoNya")
    prompt_gen  = PromptGenerator(char_card, user_card)
    prompt_gen.DiagHistory = char_card.CharacterGreeting
    prompt_gen.DiagHistory += "\nmorenico: "+ input("morenico: ")
    print(prompt_gen.DiagHistory)
    print(prompt_gen.FillingPromptGen())
    