import tkinter as tk
import random

size_ban = 670
space = int((size_ban-40)/9)
size_moji = 30
koma=["", "歩","香","桂","銀","金","角","飛","玉","と","杏","圭","全", "", "馬","竜", ""]
PROMOTE = 8
ENEMY = 16
bd=["234585432","070000060","111111111"]

class App(tk.Tk):
    def __init__(self):
        super(App, self).__init__()
        self.title("将棋")
        self.geometry("{}x{}+{}+{}".format(size_ban, size_ban, 300, 100))
        self.resizable(width=0, height=0)

        self.flag = False
        self.turn = 1
        self.unpressed = 1
        self.previous_tag = None
        self.current_tag = None
        self.previous_state = None
        self.current_state = None
        self.tmp = []
        self.candidates = []
        self.retrieves = []
        self.rtmp = []
        self.rflag = False
        self.result = [0, 0]
        self.lock = 0
        self.enlock = 0

        # Canvasの設定
        self.set_widgets()

    def set_widgets(self):
        ### 将棋盤を作る ###
        self.board = tk.Canvas(self, width=size_ban, height=size_ban, bg="Peach Puff3")
        self.board.pack()

        ### 長方形を作る ###
        # 将棋盤の情報
        # -1 -> 盤の外, 0 -> 空白
        self.board2info = [-1] * 11 + [[0, -1][i in [0, 10]] for i in range(11)] * 9 + [-1] * 11
        # {tag: position}
        self.tag2pos = {}
        # 座標からtagの変換
        self.z2tag = {}

        # 符号
        self.numstr = "123456789"
        self.kanstr = "一二三四五六七八九"
        
        # 盤の作成
        for i, y in zip(self.kanstr, range(20, size_ban-20, space)):
            for j, x in zip(self.numstr[::-1], range(20, size_ban-20, space)):
                pos = (x, y, x+space, y+space)
                tag = j + i
                self.tag2pos[tag] = pos[:2]
                self.board.create_rectangle(*pos, fill="Peach Puff3", tags=tag)
                self.z2tag[self.z_coordinate(tag)] = tag

        ### 駒を描画する ###
        # 初期配置
        setlist = [["一", "九"], ["二", "八"], ["三", "七"]]
        for count, sl in enumerate(setlist):
            for turn, i in zip([0, 1], sl):
                for j in self.numstr[::-1]:
                    tag = j + i
                    num = int(bd[count][int(j)-1])
                    self.draw_text(tag, turn, koma[num])
                    self.board2info[self.z_coordinate(tag)] = 0 if koma[num] == "" else [num + ENEMY, num][turn]
        
        self.get_board_info()
        # バインディングの設定
        self.binding()

    def binding(self):
        for tag in self.tag2pos.keys():
            self.board.tag_bind(tag, "<ButtonPress-1>", self.board_pressed)

    def run(self):
        # イベント処理が行われるまで待機
        self.mainloop()

    def draw_text(self, tag, turn, koma):
        # 駒の描画
        x, y = self.tag2pos[tag]
        if turn==0 and koma=="玉":
            koma="王"
        self.board.create_text(x+space/2, y+space/2,
                               font=("Helvetica", size_moji, "bold"),
                               angle=[180, 0][turn],
                               text=koma,
                               tags=tag)


    def z_coordinate(self, tag):
        # 座標取得
        x, y = self.numstr[::-1].index(tag[0])+1, self.kanstr.index(tag[1])+1
        return y*11 + x

    def board_pressed(self, event):
        if self.lock:
            return
        _id = self.board.find_closest(event.x, event.y)
        tag = self.board.gettags(_id[0])[0]

        # クリックされた長方形のtagから１次元の座標に変換し、
        # それをもとに盤面の情報を手に入れる。
        self.current_state = self.board2info[self.z_coordinate(tag)]
        # クリックされたのが自分の歩ならば色を変える
        # かつ、自分の歩が他に選択されていないとき
        if (self.current_state <= 15 and self.current_state >= 1) and self.unpressed:
            self.board.itemconfig(tag, fill="Peach Puff2")
            # 文字が消えるので再度文字を書く
            self.draw_text(tag, 1, koma[self.current_state])
            # クリックされた状態
            self.unpressed = 0
            # 座標と駒を保持
            self.previous_tag = tag
            self.previous_state = self.current_state
            # 候補手の探索と表示
            self.show(tag)
        elif self.current_state <= 15 and self.current_state >= 1:
            # 既に自分の歩が選択されていて、
            # 自分の他の歩を選択したとき、
            # 既に選択されているものを元に戻す。
            # その後、新しく選択した歩の色を変える。
            self.board.itemconfig(self.previous_tag, fill="Peach Puff3")
            # 文字が消えるので再度文字を書く
            self.draw_text(self.previous_tag, 1, koma[self.previous_state])
            self.board.itemconfig(tag, fill="Peach Puff2")
            self.draw_text(tag, 1, koma[self.current_state])
            self.previous_tag = tag
            # 候補手の表示の前に、先の候補手の色を元に戻す。
            for z in self.candidates:
                ctag = self.z2tag[z]
                self.board.itemconfig(ctag, fill="Peach Puff3")
            # 候補手の探索と表示
            self.show(tag)
        elif self.current_state >= 17 and self.unpressed:
            # 相手駒が選択され、かつ自分駒が選択されていない
            return
        else:
            # 歩が選択されていて、かつ空白をクリックしたときの処理
            # クリックされたところが、候補手にあるかどうか確認
            flag = self.click_is_valid(tag)
            if flag == 0:
                return
            self.current_tag = tag
            # クリックされたところが、候補手にあるので盤面の更新。
            self.update_board(tag)

    def update_board(self, tag):
        if self.turn:
            self.lock = 1
        # 候補手の色を元に戻す
        for z in self.candidates:
            ctag = self.z2tag[z]
            self.board.itemconfig(ctag, fill='Peach Puff3')
        ### 成りの条件を入れる（課題１）

        ###
        self.draw_text(tag, self.turn, koma[self.previous_state % 16])
        # 盤面の更新
        self.board2info[self.z_coordinate(tag)] = self.previous_state
        self.board2info[self.z_coordinate(self.previous_tag)] = 0
        ### 駒の取得（課題2）
        self.get_koma()
        ###
        self.board.itemconfig(self.previous_tag, fill="Peach Puff3")
        self.get_board_info(self.previous_tag, tag)
        self.unpressed = 1
        self.previous_tag = None
        self.previous_state = None
        self.candidates = []

        if self.turn:
            self.after(1000, self.AI)
        else:
            self.after(1000, self.YOU)

    def get_koma(self):
        # 駒の取得。（課題2）
        pass

    def show(self, tag):
        # 候補手の表示
        self.candidates = []
        z = self.z_coordinate(tag)
        self.search(z)
        for z in self.candidates:
            ctag = self.z2tag[z]
            self.board.itemconfig(ctag, fill="Peach Puff1")

    def search(self, z):
        # 候補手の探索。効き判定（課題3）
        for num in [-11, 11, 1, -1]:
            self.tmp = []
            self.run_search(z+num, num)
            if self.tmp:
                self.candidates += self.tmp

    def run_search(self, z, num):
        v = self.board2info[z]
        if v == 0:
            self.tmp.append(z)
            self.run_search(z+num, num)
        return -1

    def click_is_valid(self, tag):
        # クリックされたところが、候補手にあるかどうか確認
        ans = self.z_coordinate(tag)
        return 1 if ans in self.candidates else 0

    def AI(self):
        # CP側の指し手決定アルゴリズム。（課題4）
        if self.enlock:
            return
        self.turn = 0
        self.candidates = []
        while True:
            z = random.choice([i for i, v in enumerate(self.board2info) if v >= 17])
            # 動かす駒の符号
            self.previous_tag = self.z2tag[z]
            self.previous_state = self.board2info[self.z_coordinate(self.previous_tag)]
            self.search(z)
            if self.candidates:
                break

        # 候補手からランダムに選択
        z = random.choice(self.candidates)
        # 動かした後の符号
        self.current_tag = self.z2tag[z]
        self.update_board(self.current_tag)

    def YOU(self):
        # プレイヤーへ手番変更
        self.turn = 1
        self.lock = 0

    def get_board_info(self, a=None, b=None):
        # コンソールに盤面情報を出力
        tags = "" if a is None else "\n{} -> {}".format(a, b)
        board_format = " {:2d} " * 11
        print(tags, *[board_format.format(*self.board2info[i:i+11]) \
                                    for i in range(0, 121, 11)], sep='\n')

    def end_game(self):
        # ゲーム終了。詰み判定アルゴリズム。（課題5）
        self.board.unbind("<ButtonPress-1>")
        result = self.result[0] < self.result[1]
        print("Result: {} Win".format(["相手", "あなた"][result]))


if __name__ == "__main__":
    app = App()
    app.run()