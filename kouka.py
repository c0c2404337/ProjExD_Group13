import pygame
import sys
import random

# --- 設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
GRAY = (169, 169, 169)
RED = (255, 0, 0)       # こうかとん
BLUE = (0, 0, 255)      # 雑魚敵
YELLOW = (255, 215, 0)  # ボス
CYAN = (0, 255, 255)    # MP
FLASH_COLOR = (255, 255, 255) # ダメージ時の閃光
GOLD = (255, 223, 0)    # レベルアップ用

# 状態定数
STATE_MAP = "MAP"
STATE_BATTLE = "BATTLE"
STATE_ENDING = "ENDING"
STATE_GAME_OVER = "GAME_OVER"

STATE_GAME_OVER = "GAME_OVER"

# マップID
MAP_VILLAGE = 0
MAP_FIELD = 1
MAP_CAMPUS = 2

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("RPG こうく - Level Up System")
        self.clock = pygame.time.Clock()
        
        self.font = self.get_japanese_font(32)
        # 戦闘メッセージなど用の小さいフォント
        self.msg_font = self.get_japanese_font(20)

        # ゲーム進行管理（初期状態）
        self.state = STATE_MAP
        self.current_map = MAP_VILLAGE
        self.small_font = self.get_japanese_font(24)

        # プレイヤー初期状態
        self.player_pos = [50, 300]
        self.player_size = 40
        self.speed = 5
        # プレイヤーHP
        self.player_max_hp = 500
        self.player_hp = self.player_max_hp
        
        # ステータス・レベル関連（変更点）
        self.player_level = 1
        self.player_exp = 0
        self.player_next_exp = 100 # 次のレベルまで必要な経験値
        
        self.player_max_hp = 100
        self.player_hp = 100
        self.player_max_mp = 100
        self.player_mp = 100
        
        # ゲーム進行管理
        self.state = STATE_MAP
        self.current_map = MAP_VILLAGE
        self.is_boss_battle = False
        
        # 戦闘用変数
        self.enemy_hp = 0
        self.battle_message = ""
        self.battle_sub_message = ""
        # 回復回数（戦闘ごとにリセット）
        self.heals_left = 0
        # アイテム（回復薬、攻撃力アップ、防御力アップ）
        self.items = {"potion": 3, "atk": 1, "def": 1}
        # バフ（ターン数）と倍率
        self.atk_buff_turns = 0
        self.def_buff_turns = 0
        self.atk_multiplier = 1.0
        self.def_multiplier = 1.0
        # メッセージログ（戦闘内で行動ごとに更新）
        self.message_log = []
        self.max_messages = 4

        self.enemies = []
        self.battle_logs = []

    def get_japanese_font(self, size):
        font_names = ["meiryo", "msgothic", "yugothic", "hiraginosans", "notosanscjkjp"]
        available_fonts = pygame.font.get_fonts()
        for name in font_names:
            if name in available_fonts:
                return pygame.font.SysFont(name, size)
        return pygame.font.Font(None, size)

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if self.state == STATE_BATTLE:
                    if event.key == pygame.K_SPACE:
                        # プレイヤーの攻撃処理（攻撃バフを反映）
                        base_damage = random.randint(30, 60)
                        damage = int(base_damage * self.atk_multiplier)
                        self.enemy_hp -= damage
                        self.add_message(f"こうかとんの攻撃！ {damage} のダメージ！")
                        if self.enemy_hp > 0:
                            # 敵が生きていれば反撃（共通処理）
                            self.enemy_counterattack()
                        else:
                            # 敵を倒した
                            self.add_message("敵を倒した！")
                            self.end_battle()

                    elif event.key == pygame.K_h:
                        # 回復処理（使える回数がある場合のみ）
                        if self.heals_left > 0:
                            # 回復量は通常敵とボスで少し変える
                            if self.is_boss_battle:
                                heal = random.randint(500, 1000)
                            else:
                                heal = random.randint(200, 400)
                            old_hp = self.player_hp
                            self.player_hp = min(self.player_max_hp, self.player_hp + heal)
                            actual_heal = self.player_hp - old_hp
                            self.heals_left -= 1
                            self.add_message(f"こうかとんは回復した！ +{actual_heal} HP")
                            # 回復した後、敵の反撃（共通処理）
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.add_message("回復できる回数がありません！")

                    elif event.key == pygame.K_1:
                        # 回復薬使用
                        if self.items.get("potion", 0) > 0:
                            heal_amount = random.randint(100, 200)
                            old_hp = self.player_hp
                            self.player_hp = min(self.player_max_hp, self.player_hp + heal_amount)
                            actual = self.player_hp - old_hp
                            self.items["potion"] -= 1
                            self.add_message(f"回復薬を使用！ +{actual} HP")
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.add_message("回復薬がありません！")

                    elif event.key == pygame.K_2:
                        # 攻撃力アップ使用
                        if self.items.get("atk", 0) > 0:
                            self.items["atk"] -= 1
                            self.atk_buff_turns = 3
                            self.atk_multiplier = 1.5
                            self.add_message("攻撃力アップを使用！ 次の数ターン攻撃力上昇")
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.add_message("攻撃力アップがありません！")

                    elif event.key == pygame.K_3:
                        # 防御力アップ使用
                        if self.items.get("def", 0) > 0:
                            self.items["def"] -= 1
                            self.def_buff_turns = 3
                            self.def_multiplier = 0.5
                            self.add_message("防御力アップを使用！ 次の数ターン被ダメ半減")
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.add_message("防御力アップがありません！")
                    elif event.key == pygame.K_2:
                        # 攻撃力アップ使用
                        if self.items.get("atk", 0) > 0:
                            self.items["atk"] -= 1
                            self.atk_buff_turns = 3
                            self.atk_multiplier = 1.5
                            self.battle_message = "攻撃力アップを使用！ 次の数ターン攻撃力上昇"
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.battle_sub_message = "攻撃力アップがありません！"

                    elif event.key == pygame.K_3:
                        # 防御力アップ使用
                        if self.items.get("def", 0) > 0:
                            self.items["def"] -= 1
                            self.def_buff_turns = 3
                            self.def_multiplier = 0.5
                            self.battle_message = "防御力アップを使用！ 次の数ターン被ダメ半減"
                            if self.enemy_hp > 0:
                                self.enemy_counterattack()
                        else:
                            self.battle_sub_message = "防御力アップがありません！"
                elif self.state == STATE_ENDING:
                    if event.key == pygame.K_a:
                        self.execute_turn("ATTACK")
                    elif event.key == pygame.K_m:
                        self.execute_turn("MAGIC")
                    elif event.key == pygame.K_h:
                        self.execute_turn("HOIMI")
                
                elif self.state == STATE_ENDING or self.state == STATE_GAME_OVER:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                elif self.state == STATE_GAME_OVER:
                    # Rでリトライ、ESCで終了
                    if event.key == pygame.K_r:
                        self.restart()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

    def update(self):
        # --- 敵のアニメーション処理 ---
        if self.state == STATE_BATTLE:
            enemies_to_remove = []
            
            for enemy in self.enemies:
                # 1. ダメージ演出
                if enemy.get("flash_timer", 0) > 0:
                    enemy["flash_timer"] -= 1

                # 2. 死亡演出
                if enemy["hp"] <= 0:
                    if "death_timer" not in enemy:
                        enemy["death_timer"] = 60 
                        self.battle_logs.append(f"{enemy['name']}をやっつけた！")

                    enemy["death_timer"] -= 1
                    
                    # タイマー0で消滅（経験値獲得）
                    if enemy["death_timer"] <= 0:
                        self.gain_exp(enemy["xp"]) # 経験値処理へ
                        enemies_to_remove.append(enemy)

            # 消滅実行
            for enemy in enemies_to_remove:
                if enemy in self.enemies:
                    self.enemies.remove(enemy)
            
            if len(self.enemies) == 0:
                self.end_battle(win=True)


        # --- 移動画面処理 ---
        if self.state == STATE_MAP:
            keys = pygame.key.get_pressed()
            moved = False
            
            if keys[pygame.K_LEFT]:
                self.player_pos[0] -= self.speed
                moved = True
            if keys[pygame.K_RIGHT]:
                self.player_pos[0] += self.speed
                moved = True
            if keys[pygame.K_UP]:
                self.player_pos[1] -= self.speed
                moved = True
            if keys[pygame.K_DOWN]:
                self.player_pos[1] += self.speed
                moved = True

            self.check_map_transition()
            if moved and self.current_map == MAP_FIELD:
                self.check_random_encounter()
            
            if self.current_map == MAP_CAMPUS and self.player_pos[0] > 700:
                self.start_battle(is_boss=True)

    # --- 重要：経験値とレベルアップ処理 ---
    def gain_exp(self, amount):
        self.player_exp += amount
        self.battle_logs.append(f"{amount} Expを獲得！")
        
        # レベルアップ判定
        while self.player_exp >= self.player_next_exp:
            self.player_level += 1
            self.player_exp -= self.player_next_exp # 現在のExpを消費して次のレベルへ
            self.player_next_exp = int(self.player_next_exp * 1.5) # 必要経験値増加
            
            # ステータス上昇
            self.player_max_hp += 20
            self.player_max_mp += 10
            
            # 全回復（ボーナス）
            self.player_hp = self.player_max_hp
            self.player_mp = self.player_max_mp
            
            self.battle_logs.append(f"レベルアップ！ Lv{self.player_level} になった！")
            self.battle_logs.append("最大HPとMPが増え、全回復した！")

    def check_map_transition(self):
        if self.player_pos[0] > SCREEN_WIDTH:
            if self.current_map < MAP_CAMPUS:
                self.current_map += 1
                self.player_pos[0] = 10
            else:
                self.player_pos[0] = SCREEN_WIDTH - self.player_size
        elif self.player_pos[0] < 0:
            if self.current_map > MAP_VILLAGE:
                self.current_map -= 1
                self.player_pos[0] = SCREEN_WIDTH - 10
            else:
                self.player_pos[0] = 0

    def check_random_encounter(self):
        if random.randint(0, 100) < 1:
            self.start_battle(is_boss=False)

    def start_battle(self, is_boss):
        self.state = STATE_BATTLE
        self.is_boss_battle = is_boss
        # 回復を使える回数を設定
        self.heals_left = 3 if not is_boss else 5
        # メッセージログをリセットして見やすくする
        self.message_log = []
        self.enemies = []
        self.battle_logs = ["敵が現れた！"]

        if is_boss:
            self.enemy_hp = 500
            self.add_message("「単位を奪う悪の組織」が現れた！")
            self.enemies.append({
                "name": "悪の組織",
                "hp": 1000, "max_hp": 1000, "atk": 40, "xp": 5000, # ボスは高経験値
                "color": YELLOW, "rect": pygame.Rect(300, 50, 200, 200),
                "flash_timer": 0
            })
        else:
            self.enemy_hp = 100
            self.add_message("「未提出の課題」が現れた！")
        # 操作説明を最初に表示
        self.add_message("操作: SPACE 攻撃  H 回復  1:回復薬 2:攻撃UP 3:防御UP")


    def end_battle(self):
        if self.is_boss_battle:
            self.state = STATE_ENDING
        else:
            self.state = STATE_MAP
            self.battle_message = ""
            # 戦闘終了後、再エンカウント防止のために少し座標をずらすなどの処理を入れるとより良い
            pygame.time.wait(500) # 少しウェイトを入れる

    def game_over(self):
        """プレイヤーのHPが0になったときの処理"""
        self.state = STATE_GAME_OVER

    def restart(self):
        """簡易リスタート（村に戻りHP回復）"""
        self.state = STATE_MAP
        self.current_map = MAP_VILLAGE
        self.player_pos = [50, 300]
        self.player_hp = self.player_max_hp
        self.enemy_hp = 0
        self.battle_message = ""
        self.battle_sub_message = ""
        self.heals_left = 0
        self.clear_messages()
        # アイテム・バフもリセット
        self.items = {"potion": 3, "atk": 1, "def": 1}
        self.atk_buff_turns = 0
        self.def_buff_turns = 0
        self.atk_multiplier = 1.0
        self.def_multiplier = 1.0

    def enemy_counterattack(self):
        """敵の反撃処理（防御バフを適用、バフターンを減らす）"""
        if self.enemy_hp <= 0:
            return
        # 敵の攻撃ダメージはボスか通常で変える
        if self.is_boss_battle:
            edamage = random.randint(30, 80)
        else:
            edamage = random.randint(10, 30)
        # 防御バフを適用
        edamage = max(1, int(edamage * self.def_multiplier))
        self.player_hp -= edamage
        # 表示用メッセージを追加
        self.add_message(f"敵の反撃！ {edamage} のダメージ！ (残りHP: {max(0, self.player_hp)}) 回復残り: {self.heals_left} 回復薬: {self.items.get('potion',0)}")
        if self.player_hp <= 0:
            self.game_over()
        # バフのターンを減らす
        if self.atk_buff_turns > 0:
            self.atk_buff_turns -= 1
            if self.atk_buff_turns == 0:
                self.atk_multiplier = 1.0
        if self.def_buff_turns > 0:
            self.def_buff_turns -= 1
            if self.def_buff_turns == 0:
                self.def_multiplier = 1.0

    def add_message(self, text):
        """メッセージをログに追加し、最大長を超えたら古いものを削除する"""
        self.message_log.append(text)
        # 最新メッセージのみ保持
        if len(self.message_log) > self.max_messages:
            self.message_log = self.message_log[-self.max_messages:]

    def clear_messages(self):
        self.message_log = []

            num_enemies = random.randint(1, 3)
            for i in range(num_enemies):
                x_pos = 150 + i * 180
                self.enemies.append({
                    "name": f"課題{i+1}",
                    "hp": 50, "max_hp": 50, "atk": 10, "xp": 40, # 雑魚は40Exp
                    "color": BLUE, "rect": pygame.Rect(x_pos, 100, 100, 100),
                    "flash_timer": 0
                })

    def execute_turn(self, action_type):
        self.battle_logs = [] 
        valid_targets = [e for e in self.enemies if e["hp"] > 0]

        if not valid_targets and len(self.enemies) == 0:
            return

        # --- プレイヤー行動 ---
        # レベルに応じた威力補正
        level_bonus = (self.player_level - 1) * 2

        if action_type == "HOIMI":
            if self.player_mp >= 10:
                self.player_mp -= 10
                base_heal = random.randint(30, 50)
                heal_amount = base_heal + level_bonus # レベルで回復量も増える
                
                old_hp = self.player_hp
                self.player_hp = min(self.player_max_hp, self.player_hp + heal_amount)
                recovered = self.player_hp - old_hp
                self.battle_logs.append(f"ホイミ！ HPが{recovered}回復！")
            else:
                self.battle_logs.append("MPが足りない！")

        elif action_type == "MAGIC":
            if self.player_mp >= 30:
                if valid_targets:
                    target = valid_targets[0]
                    self.player_mp -= 30
                    
                    base_dmg = random.randint(50, 80)
                    damage = base_dmg + (level_bonus * 2) # 魔法はレベル恩恵大
                    
                    if random.randint(0, 100) < 10:
                        damage = int(damage * 1.5)
                        self.battle_logs.append("会心の一撃！！")
                    
                    target["hp"] -= damage
                    target["flash_timer"] = 10 
                    self.battle_logs.append(f"魔法攻撃！{target['name']}に{damage}ダメ！")
            else:
                self.battle_logs.append("MPが足りない！")

        elif action_type == "ATTACK":
            if valid_targets:
                target = valid_targets[0]
                base_dmg = random.randint(20, 30)
                damage = base_dmg + level_bonus

                if random.randint(0, 100) < 15:
                    damage = damage * 2
                    self.battle_logs.append("会心の一撃！！")

                target["hp"] -= damage
                target["flash_timer"] = 10 
                self.battle_logs.append(f"攻撃！ {target['name']}に{damage}ダメ！")

        # --- 敵の反撃 ---
        surviving_enemies = [e for e in self.enemies if e["hp"] > 0]
        total_dmg = 0
        for enemy in surviving_enemies:
            hit_chance = random.randint(0, 100)
            if hit_chance < 20: 
                self.battle_logs.append(f"{enemy['name']}の攻撃ミス！")
            else:
                dmg = random.randint(enemy["atk"] - 3, enemy["atk"] + 3)
                total_dmg += dmg
        
        if total_dmg > 0:
            self.player_hp -= total_dmg
            self.battle_logs.append(f"敵の攻撃！ 計{total_dmg}のダメージ！")

        if self.player_hp <= 0:
            self.player_hp = 0
            self.end_battle(win=False)

    def end_battle(self, win):
        if win:
            if self.is_boss_battle:
                self.state = STATE_ENDING
            else:
                self.state = STATE_MAP
        else:
            self.state = STATE_GAME_OVER

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == STATE_MAP:
            color = GREEN
            if self.current_map == MAP_VILLAGE: color = (100, 200, 100)
            elif self.current_map == MAP_CAMPUS: color = GRAY
            pygame.draw.rect(self.screen, color, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(self.screen, RED, (*self.player_pos, self.player_size, self.player_size))
            
            # マップ画面のステータス表示（Lv追加）
            status_str = f"Lv:{self.player_level}  HP:{self.player_hp}/{self.player_max_hp}"
            status = self.font.render(status_str, True, BLACK)
            self.screen.blit(status, (550, 20))

        elif self.state == STATE_BATTLE:
            for enemy in self.enemies:
                if "death_timer" in enemy:
                    if (enemy["death_timer"] // 5) % 2 == 0:
                        pygame.draw.rect(self.screen, (100, 0, 0), enemy["rect"])
                else:
                    draw_color = enemy["color"]
                    if enemy.get("flash_timer", 0) > 0:
                        draw_color = FLASH_COLOR
                    pygame.draw.rect(self.screen, draw_color, enemy["rect"])
                    
                    if enemy["hp"] > 0:
                        hp_rate = max(0, enemy["hp"] / enemy["max_hp"])
                        pygame.draw.rect(self.screen, RED, (enemy["rect"].x, enemy["rect"].y - 10, enemy["rect"].width, 5))
                        pygame.draw.rect(self.screen, GREEN, (enemy["rect"].x, enemy["rect"].y - 10, enemy["rect"].width * hp_rate, 5))

            # UI描画
            ui_y_start = 350
            ui_height = SCREEN_HEIGHT - ui_y_start
            pygame.draw.rect(self.screen, BLACK, (0, ui_y_start, SCREEN_WIDTH, ui_height))
            pygame.draw.rect(self.screen, WHITE, (0, ui_y_start, SCREEN_WIDTH, ui_height), 2)


            # メッセージログ（最新のメッセージを上から順に表示）
            y = 420
            for m in self.message_log[-self.max_messages:]:
                msg = self.msg_font.render(m, True, WHITE)
                self.screen.blit(msg, (50, y))
                y += 22

            hp_msg = self.msg_font.render(f"敵HP: {self.enemy_hp}", True, WHITE)
            self.screen.blit(hp_msg, (50, y))

            # プレイヤーHP表示
            p_hp_msg = self.msg_font.render(f"プレイヤーHP: {self.player_hp}", True, WHITE)
            self.screen.blit(p_hp_msg, (400, y))

            # 回復残り表示
            heal_msg = self.msg_font.render(f"回復残り: {self.heals_left}", True, WHITE)
            self.screen.blit(heal_msg, (400, y+30))

            # アイテム表示
            item_msg = self.msg_font.render(f"回復薬: {self.items.get('potion',0)}  攻撃UP: {self.items.get('atk',0)}  防御UP: {self.items.get('def',0)}", True, WHITE)
            self.screen.blit(item_msg, (50, 395))

            # バフ残り表示
            buff_msg = self.msg_font.render(f"ATK+:{self.atk_buff_turns}  DEF-:{self.def_buff_turns}", True, WHITE)
            self.screen.blit(buff_msg, (400, y+60))

            # ステータス表示（Lv, Exp追加）
            hp_color = WHITE if self.player_hp > 30 else RED
            
            # LvとExp
            lv_text = f"Lv: {self.player_level}"
            exp_text = f"Exp: {self.player_exp}/{self.player_next_exp}"
            self.screen.blit(self.font.render(lv_text, True, GOLD), (30, ui_y_start + 15))
            self.screen.blit(self.small_font.render(exp_text, True, WHITE), (120, ui_y_start + 20))

            # HPとMP
            hp_text = f"HP: {self.player_hp}/{self.player_max_hp}"
            mp_text = f"MP: {self.player_mp}/{self.player_max_mp}"
            self.screen.blit(self.font.render(hp_text, True, hp_color), (300, ui_y_start + 15))
            self.screen.blit(self.font.render(mp_text, True, CYAN), (550, ui_y_start + 15))

            # コマンド
            cmd_text = "[A]たたかう  [M]まほう(30)  [H]ホイミ(10)"
            self.screen.blit(self.font.render(cmd_text, True, YELLOW), (30, ui_y_start + 60))

            # 区切り線
            line_y = ui_y_start + 100
            pygame.draw.line(self.screen, WHITE, (0, line_y), (SCREEN_WIDTH, line_y), 1)

            # ログ
            display_logs = self.battle_logs[-5:] 
            for i, log in enumerate(display_logs):
                log_color = WHITE
                if "会心" in log: log_color = YELLOW
                if "やっつけた" in log: log_color = (255, 100, 100)
                if "レベルアップ" in log: log_color = GOLD # レベルアップは金色
                
                txt = self.small_font.render(log, True, log_color)
                self.screen.blit(txt, (30, line_y + 10 + i * 28))

        elif self.state == STATE_ENDING:
            self.screen.fill(WHITE)
            end_text1 = self.font.render("単位は守られた！", True, BLACK)
            end_text2 = self.font.render("Thank you for playing.", True, BLACK)
           
            self.screen.blit(end_text1, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 20))
            self.screen.blit(end_text2, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 30))

        elif self.state == STATE_GAME_OVER:
            # ゲームオーバー画面
            self.screen.fill(BLACK)
            go_text = self.font.render("GAME OVER", True, RED)
            info_text = self.font.render("R: リトライ    ESC: 終了", True, WHITE)
            self.screen.blit(go_text, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 - 30))
            self.screen.blit(info_text, (SCREEN_WIDTH//2 - 140, SCREEN_HEIGHT//2 + 30))

            msg = self.font.render("MISSION COMPLETE!", True, BLACK)
            self.screen.blit(msg, (200, 300))

        elif self.state == STATE_GAME_OVER:
            self.screen.fill(BLACK)
            msg = self.font.render("GAME OVER...", True, RED)
            self.screen.blit(msg, (300, 300))

        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()