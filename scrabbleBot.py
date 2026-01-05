import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class ScrabbleGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Scrabble Game Tracker")
        self.root.configure(bg="#333333")

        # --- Game State Variables ---
        self.letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.start_count = 10
        self.game_active = False
        self.current_turn = None # "user" or "opponent"
        self.draw_phase = False # If True, clicks on bag add to hand
        self.temp_drawn_tiles = [] # Stores tiles drawn during the draw phase
        
        # Data storage
        self.tile_data = {} 
        self.user_hand = ["", "", "", "", "", "", ""]
        self.opp_hand = ["?", "?", "?", "?", "?", "?", "?"]

        # --- UI LAYOUT ---

        # 1. Header / Control Panel
        self.control_frame = tk.Frame(root, bg="#333333")
        self.control_frame.pack(fill="x", padx=10, pady=10)

        self.btn_start = tk.Button(self.control_frame, text="START GAME", command=self.start_game_sequence, 
                                   bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
        self.btn_start.pack(side="left", padx=5)

        self.btn_reset = tk.Button(self.control_frame, text="RESET", command=self.reset_game, 
                                   bg="#d9534f", fg="white", font=("Arial", 12, "bold"))
        self.btn_reset.pack(side="right", padx=5)

        # Status Label (Important for instructions)
        self.lbl_status = tk.Label(root, text="Setup Phase: Set your hand and adjust bag if needed.", 
                                   font=("Arial", 14), bg="#333333", fg="#4a90e2")
        self.lbl_status.pack(pady=5)

        # 2. Main Tile Bag (The Grid)
        self.pool_frame = tk.Frame(root, bg="#333333")
        self.pool_frame.pack(padx=10, pady=5)
        self.create_main_grid()

        # Separator
        ttk.Separator(root, orient='horizontal').pack(fill='x', pady=10)

        # 3. Action Area (Inputting words / Proceeding)
        self.action_frame = tk.Frame(root, bg="#444444", bd=2, relief="groove")
        self.action_frame.pack(fill="x", padx=20, pady=5)
        
        # Widgets for playing a word (Hidden initially)
        self.lbl_action = tk.Label(self.action_frame, text="Enter Word Played:", bg="#444444", fg="white", font=("Arial", 12))
        self.entry_word = tk.Entry(self.action_frame, font=("Arial", 12))
        self.btn_play_word = tk.Button(self.action_frame, text="Submit Play", command=self.submit_play, bg="#F0AD4E")
        
        # Widgets for proceeding (Hidden initially)
        self.btn_proceed = tk.Button(self.action_frame, text="Finish Drawing & Proceed", command=self.proceed_turn, bg="#5bc0de")

        # 4. Hands Area
        self.hands_container = tk.Frame(root, bg="#2b2b2b")
        self.hands_container.pack(fill="x", padx=10, pady=(10, 20), expand=True)

        # User Hand
        self.user_frame = tk.Frame(self.hands_container, bg="#2b2b2b")
        self.user_frame.pack(side="left", fill="both", expand=True, padx=10)
        tk.Label(self.user_frame, text="MY HAND", font=("Arial", 12, "bold"), bg="#2b2b2b", fg="white").pack()
        self.user_tiles_vis = tk.Frame(self.user_frame, bg="#2b2b2b")
        self.user_tiles_vis.pack(pady=5)
        self.btn_set_hand = tk.Button(self.user_frame, text="Edit Hand", command=self.open_hand_selector, bg="#555")
        self.btn_set_hand.pack(pady=5)

        # Opponent Hand
        self.opp_frame = tk.Frame(self.hands_container, bg="#2b2b2b")
        self.opp_frame.pack(side="right", fill="both", expand=True, padx=10)
        tk.Label(self.opp_frame, text="OPPONENT HAND", font=("Arial", 12, "bold"), bg="#2b2b2b", fg="white").pack()
        self.opp_tiles_vis = tk.Frame(self.opp_frame, bg="#2b2b2b")
        self.opp_tiles_vis.pack(pady=5)
        
        self.refresh_hands_ui()

    # --- UI BUILDING BLOCKS ---

    def create_tile_widget(self, parent, letter, count=None, size_scale=1.0, click_callback=None):
        w = int(50 * size_scale)
        h = int(60 * size_scale)
        font_sz = int(18 * size_scale)
        
        frame = tk.Frame(parent, bg="#F5DEB3", bd=2, relief="raised", width=w, height=h)
        frame.grid_propagate(False)
        frame.pack_propagate(False)

        lbl_letter = tk.Label(frame, text=letter, font=("Arial", font_sz, "bold"), bg="#F5DEB3", fg="black")
        lbl_letter.pack(expand=True)

        lbl_count = None
        if count is not None:
            lbl_count = tk.Label(frame, text=str(count), font=("Arial", int(9*size_scale)), bg="#F5DEB3", fg="#555555")
            lbl_count.pack(side="bottom")

        # Bind events
        if click_callback:
            def on_click(e): click_callback()
            frame.bind("<Button-1>", on_click)
            lbl_letter.bind("<Button-1>", on_click)
            if lbl_count: lbl_count.bind("<Button-1>", on_click)

        return frame, lbl_letter, lbl_count

    def create_main_grid(self):
        max_col = 9
        for i, letter in enumerate(self.letters):
            r, c = divmod(i, max_col)
            container = tk.Frame(self.pool_frame, bg="#333333")
            container.grid(row=r, column=c, padx=3, pady=3)
            
            f, l_lbl, c_lbl = self.create_tile_widget(
                container, letter, count=self.start_count, size_scale=0.8,
                click_callback=lambda x=letter: self.handle_bag_click(x)
            )
            f.pack()
            self.tile_data[letter] = {"count": self.start_count, "frame": f, "cnt_lbl": c_lbl, "let_lbl": l_lbl}

    # --- LOGIC HANDLERS ---

    def handle_bag_click(self, letter):
        """ Handles clicking a tile in the main bag grid """
        data = self.tile_data[letter]
        
        # Logic 1: Setup Phase (Simple decrement)
        if not self.game_active:
            if data["count"] > 0:
                data["count"] -= 1
                self.update_tile_visual(letter)
            return

        # Logic 2: Play Phase (Bag is Locked)
        if not self.draw_phase:
            messagebox.showinfo("Locked", "The bag is locked until you submit a played word.")
            return

        # Logic 3: Draw Phase (Refill hand)
        if self.draw_phase and data["count"] > 0:
            data["count"] -= 1
            self.update_tile_visual(letter)
            self.temp_drawn_tiles.append(letter)
            # Update status to show what was drawn
            self.lbl_status.config(text=f"Drawing: {', '.join(self.temp_drawn_tiles)}")

    def update_tile_visual(self, letter):
        data = self.tile_data[letter]
        data["cnt_lbl"].config(text=str(data["count"]))
        if data["count"] == 0:
            gray = "#999999"
            data["frame"].config(bg=gray, relief="sunken")
            data["let_lbl"].config(bg=gray, fg="#666666")
            data["cnt_lbl"].config(bg=gray, fg="#666666")
        else:
            # ensure it looks active
            wood = "#F5DEB3"
            data["frame"].config(bg=wood, relief="raised")
            data["let_lbl"].config(bg=wood, fg="black")
            data["cnt_lbl"].config(bg=wood, fg="#555555")

    # --- GAME FLOW ---

    def start_game_sequence(self):
        # 1. Hide Start Button
        self.btn_start.pack_forget()
        self.btn_set_hand.config(state="disabled") # Lock manual hand editing
        self.game_active = True

        # 2. Select Who Starts
        choice_win = tk.Toplevel(self.root)
        choice_win.title("Who starts?")
        choice_win.geometry("300x150")
        
        tk.Label(choice_win, text="Who plays first?", font=("Arial", 12)).pack(pady=20)
        
        def set_starter(who):
            self.current_turn = who
            choice_win.destroy()
            self.initiate_turn()

        tk.Button(choice_win, text="ME (User)", command=lambda: set_starter("user"), width=10).pack(side="left", padx=20, pady=20)
        tk.Button(choice_win, text="OPPONENT", command=lambda: set_starter("opponent"), width=10).pack(side="right", padx=20, pady=20)

    def initiate_turn(self):
        """ Sets up the UI for the start of a turn """
        self.draw_phase = False
        self.temp_drawn_tiles = []
        self.dim_bag(True) # Visual lock of bag

        # Show input fields
        self.btn_proceed.pack_forget()
        self.lbl_action.pack(side="left", padx=5)
        self.entry_word.pack(side="left", padx=5)
        self.btn_play_word.pack(side="left", padx=5)
        
        self.entry_word.delete(0, tk.END)

        if self.current_turn == "user":
            self.lbl_status.config(text="YOUR TURN: Enter the word you played.", fg="#4CAF50")
        else:
            self.lbl_status.config(text="OPPONENT'S TURN: Enter the word they played.", fg="#d9534f")

    def submit_play(self):
        """ Triggered when 'Submit Play' is clicked """
        word = self.entry_word.get().upper().strip()
        if not word:
            messagebox.showerror("Error", "Please enter a word.")
            return

        # Remove letters from hand
        if self.current_turn == "user":
            # Check if user has letters
            temp_hand = self.user_hand.copy()
            possible = True
            for char in word:
                if char in temp_hand:
                    temp_hand.remove(char)
                elif "" in temp_hand: # Blank used (represented as empty string in my logic, usually)
                    temp_hand.remove("") 
                else:
                    # Logic note: Standard Scrabble has blanks. 
                    # If letter not found, we assume a blank or error. 
                    # For this simple app, we will just warn but allow forcing.
                    pass
            
            self.user_hand = temp_hand

        else: # Opponent
            # Remove letters. If letter exists, remove it. If not, remove a '?'
            for char in word:
                if char in self.opp_hand:
                    self.opp_hand.remove(char)
                elif "?" in self.opp_hand:
                    self.opp_hand.remove("?")
                else:
                    # Hand empty or ran out of tiles
                    pass

        self.refresh_hands_ui()
        self.start_draw_phase()

    def start_draw_phase(self):
        """ Setup UI for drawing from bag """
        self.draw_phase = True
        
        # Hide play widgets, Show proceed widget
        self.lbl_action.pack_forget()
        self.entry_word.pack_forget()
        self.btn_play_word.pack_forget()
        
        self.btn_proceed.pack(pady=5)
        
        self.dim_bag(False) # Unlock bag visually
        
        txt = "Update the Bag: Click the letters that "
        txt += "YOU drew." if self.current_turn == "user" else "THEY drew."
        self.lbl_status.config(text=txt, fg="#e67e22")

    def proceed_turn(self):
        """ Finalize draw and switch turns """
        # Add temp tiles to current player's hand
        if self.current_turn == "user":
            self.user_hand.extend(self.temp_drawn_tiles)
        else:
            self.opp_hand.extend(self.temp_drawn_tiles)
            
        self.refresh_hands_ui()
        
        # Switch Turn
        if self.current_turn == "user":
            self.current_turn = "opponent"
        else:
            self.current_turn = "user"
            
        self.initiate_turn()

    # --- UTILS ---

    def dim_bag(self, dim):
        # Visual effect to show if bag is active or not
        bg_color = "#222222" if dim else "#333333"
        self.pool_frame.config(bg=bg_color)
        # We don't actually disable the widgets, we just handle logic in the click handler

    def refresh_hands_ui(self):
        # Clear
        for w in self.user_tiles_vis.winfo_children(): w.destroy()
        for w in self.opp_tiles_vis.winfo_children(): w.destroy()

        # User
        for char in self.user_hand:
            display = char if char else " " # Handle empty string as blank
            cont = tk.Frame(self.user_tiles_vis, bg="#2b2b2b")
            cont.pack(side="left", padx=2)
            f, _, _ = self.create_tile_widget(cont, display, size_scale=0.7)
            f.pack()

        # Opponent
        for char in self.opp_hand:
            cont = tk.Frame(self.opp_tiles_vis, bg="#2b2b2b")
            cont.pack(side="left", padx=2)
            f, _, _ = self.create_tile_widget(cont, char, size_scale=0.7)
            f.pack()

    def open_hand_selector(self):
        # Only allowed before game starts
        popup = tk.Toplevel(self.root)
        popup.title("Set Hand")
        popup.geometry("400x150")
        
        tk.Label(popup, text="Initial Hand Setup (7 Tiles)", pady=10).pack()
        fr = tk.Frame(popup)
        fr.pack()
        
        options = [""] + list(self.letters)
        boxes = []
        for i in range(7):
            cb = ttk.Combobox(fr, values=options, width=3, state="readonly")
            cb.pack(side="left", padx=2)
            # set current
            try:
                cb.set(self.user_hand[i])
            except: pass
            boxes.append(cb)
            
        def save():
            new_h = [b.get() for b in boxes]
            self.user_hand = new_h
            self.refresh_hands_ui()
            popup.destroy()
            
        tk.Button(popup, text="Save", command=save, bg="#4CAF50", fg="white").pack(pady=10)

    def reset_game(self):
        if not messagebox.askyesno("Reset", "Are you sure? This will clear everything."):
            return
            
        self.game_active = False
        self.current_turn = None
        self.user_hand = ["", "", "", "", "", "", ""]
        self.opp_hand = ["?", "?", "?", "?", "?", "?", "?"]
        
        # Reset Bag Counts
        for letter, data in self.tile_data.items():
            data["count"] = self.start_count
            self.update_tile_visual(letter)
            
        # UI Resets
        self.btn_start.pack(side="left", padx=5)
        self.btn_set_hand.config(state="normal")
        self.lbl_action.pack_forget()
        self.entry_word.pack_forget()
        self.btn_play_word.pack_forget()
        self.btn_proceed.pack_forget()
        self.lbl_status.config(text="Setup Phase: Set your hand and adjust bag if needed.", fg="#4a90e2")
        self.refresh_hands_ui()
        self.dim_bag(False)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x700")
    app = ScrabbleGame(root)
    root.mainloop()