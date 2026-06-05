import time
import requests
import os
import sys
import io
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk

class MalGuiImporter:
    def __init__(self, root):
        self.root = root
        self.root.title("MAL List Importer")
        self.root.geometry("1000x800")
        self.root.configure(bg="#1e1e1e")
        
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background="#1e1e1e", foreground="#e0e0e0")
        style.configure("TLabel", background="#1e1e1e", foreground="#e0e0e0")
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TPanedwindow", background="#1e1e1e")
        
        self.filename = ""
        self.all_anime = []
        self.current_idx = 0
        
        self.selected_mal_id = "0"
        self.selected_title = ""
        self.selected_type = "TV"
        self.selected_episodes = "0"
        
        self.anime_xml_dict = {}
        
        self.load_batch_file()
        self.setup_ui()
        self.process_next_anime()

    def load_batch_file(self):
        self.filename = filedialog.askopenfilename(
            title="Select Anime Batch File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not self.filename:
            sys.exit(0)
            
        self.root.title("MAL List Importer - " + os.path.basename(self.filename))
            
        with open(self.filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line or line[0] == "[" or line[0] == "#":
                continue
            
            if "LiveAction" in line and "S1" not in line:
                line = line.replace("LiveAction", "").strip()

            parts = line.split(" ")
            last_part = parts[-1]
            base_title = " ".join(parts[:-1])

            if ("S" in last_part or "M" in last_part) and any(c.isdigit() for c in last_part):
                sub_sections = last_part.split(".")
                for section in sub_sections:
                    if section[0] == "S":
                        s_num = section.replace("S", "")
                        if s_num.isdigit():
                            suffix = " Season " + s_num if s_num != "1" else ""
                            self.all_anime.append((base_title + suffix).strip())
                    elif section[0] == "M":
                        m_num = section.replace("M", "")
                        self.all_anime.append((base_title + " Movie " + m_num).strip())
            else:
                self.all_anime.append(line)

    def setup_ui(self):
        self.top_frame = tk.Frame(self.root, bg="#1e1e1e", pady=10, padx=10)
        self.top_frame.pack(fill="x")
        
        self.progress_label = tk.Label(self.top_frame, text="Progress: 0/0", font=("Arial", 12, "bold"), bg="#1e1e1e", fg="#4fc1ff")
        self.progress_label.pack(side="left", padx=10)
        
        search_container = tk.Frame(self.top_frame, bg="#1e1e1e")
        search_container.pack(side="right")
        
        tk.Label(search_container, text="Manual Search:", font=("Arial", 11), bg="#1e1e1e", fg="#cccccc").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_container, textvariable=self.search_var, font=("Arial", 12), width=35, bg="#3c3c3c", fg="#ffffff", insertbackground="white", borderwidth=0)
        self.search_entry.pack(side="left", padx=5, ipady=4)
        self.search_entry.bind("<Return>", self.manual_search)
        
        search_btn = tk.Button(search_container, text="Search API", command=self.manual_search, bg="#0e639c", fg="white", font=("Arial", 10, "bold"), borderwidth=0, padx=10, pady=2, cursor="hand2")
        search_btn.pack(side="left", padx=5)
        
        self.main_frame = ttk.Panedwindow(self.root, orient="horizontal")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.list_frame = tk.Frame(self.main_frame, bg="#1e1e1e")
        self.main_frame.add(self.list_frame, weight=3)
        
        tk.Label(self.list_frame, text="Search Results (Select One):", font=("Arial", 11, "bold"), bg="#1e1e1e", fg="#cccccc").pack(anchor="w", pady=5)
        self.results_box = tk.Listbox(self.list_frame, font=("Arial", 11), bg="#252526", fg="#d4d4d4", selectbackground="#094771", selectforeground="#ffffff", borderwidth=0, highlightthickness=1, highlightcolor="#3e3e42", highlightbackground="#3e3e42")
        self.results_box.pack(fill="both", expand=True)
        self.results_box.bind("<<ListboxSelect>>", self.on_select_anime)
        
        self.right_frame = tk.Frame(self.main_frame, bg="#1e1e1e")
        self.main_frame.add(self.right_frame, weight=2)
        
        self.img_label = tk.Label(self.right_frame, bg="#1e1e1e")
        self.img_label.pack(pady=10)
        
        self.details_label = tk.Label(self.right_frame, text="", justify="center", font=("Arial", 11), bg="#1e1e1e", fg="#ffffff")
        self.details_label.pack(pady=5)
        
        self.control_frame = tk.Frame(self.root, bg="#1e1e1e", pady=15)
        self.control_frame.pack(fill="x", side="bottom")
        
        self.status_var = tk.StringVar(value="Completed")
        status_frame = tk.Frame(self.control_frame, bg="#1e1e1e")
        status_frame.pack(pady=5)
        
        for st in ["Completed", "Watching", "On-Hold", "Plan to Watch", "Dropped"]:
            tk.Radiobutton(status_frame, text=st, variable=self.status_var, value=st, indicatoron=False, font=("Arial", 11, "bold"), width=12, bg="#333333", fg="#cccccc", selectcolor="#0e639c", activebackground="#444444", activeforeground="#ffffff", borderwidth=0, cursor="hand2").pack(side="left", padx=4)
            
        self.rating_var = tk.StringVar(value="0")
        rating_frame = tk.Frame(self.control_frame, bg="#1e1e1e")
        rating_frame.pack(pady=10)
        
        tk.Radiobutton(rating_frame, text="0 (Unrated)", variable=self.rating_var, value="0", indicatoron=False, font=("Arial", 11, "bold"), width=20, bg="#333333", fg="#cccccc", selectcolor="#094771", activebackground="#444444", activeforeground="#ffffff", borderwidth=0, cursor="hand2").pack(side="top", pady=(0, 8))
        
        rating_grid = tk.Frame(rating_frame, bg="#1e1e1e")
        rating_grid.pack()
        
        ratings_data = [
            ("1", "(1) Appalling"),
            ("2", "(2) Horrible"),
            ("3", "(3) Very Bad"),
            ("4", "(4) Bad"),
            ("5", "(5) Average"),
            ("6", "(6) Fine"),
            ("7", "(7) Good"),
            ("8", "(8) Very Good"),
            ("9", "(9) Great"),
            ("10", "(10) Masterpiece")
        ]
        
        for i, data_tuple in enumerate(ratings_data):
            val = data_tuple[0]
            text = data_tuple[1]
            row_idx = 0 if i < 5 else 1
            col_idx = i % 5
            tk.Radiobutton(rating_grid, text=text, variable=self.rating_var, value=val, indicatoron=False, font=("Arial", 10, "bold"), width=15, bg="#333333", fg="#cccccc", selectcolor="#094771", activebackground="#444444", activeforeground="#ffffff", borderwidth=0, cursor="hand2").grid(row=row_idx, column=col_idx, padx=4, pady=4)
            
        action_frame = tk.Frame(self.control_frame, bg="#1e1e1e")
        action_frame.pack(pady=15)
        
        tk.Button(action_frame, text="◄ Go Back", command=self.go_back, font=("Arial", 12, "bold"), bg="#d97706", fg="white", width=12, height=2, borderwidth=0, cursor="hand2").pack(side="left", padx=10)
        tk.Button(action_frame, text="Submit & Next", command=self.submit_current, font=("Arial", 12, "bold"), bg="#16a34a", fg="white", width=20, height=2, borderwidth=0, cursor="hand2").pack(side="left", padx=10)
        tk.Button(action_frame, text="Skip Title", command=self.skip_current, font=("Arial", 12, "bold"), bg="#dc2626", fg="white", width=20, height=2, borderwidth=0, cursor="hand2").pack(side="left", padx=10)

    def manual_search(self, event=None):
        query = self.search_var.get().strip()
        if not query:
            return
            
        self.results_box.delete(0, tk.END)
        self.img_label.config(image="")
        self.details_label.config(text="Searching API...")
        self.root.update()
        
        self.current_results = self.search_mal_api(query)
        self.details_label.config(text="")
        
        if self.current_results:
            for res in self.current_results:
                t = res.get("title", "Unknown")
                t_type = res.get("type", "TV")
                year = res.get("year") or "N/A"
                self.results_box.insert(tk.END, t + " (" + t_type + ", " + str(year) + ")")
            self.results_box.selection_set(0)
            self.on_select_anime(None)
        else:
            self.results_box.insert(tk.END, "No database entries found for this query.")
            self.selected_mal_id = "0"
            self.selected_title = query
            self.selected_type = "TV"
            self.selected_episodes = "0"

    def search_mal_api(self, query):
        url = "https://api.jikan.moe/v4/anime"
        params = {"q": query, "limit": 7}
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                return res.json().get("data", [])
            elif res.status_code == 429:
                time.sleep(2)
                return self.search_mal_api(query)
        except Exception:
            pass
        return []

    def process_next_anime(self):
        if self.current_idx >= len(self.all_anime):
            self.save_xml_output()
            return
            
        self.results_box.delete(0, tk.END)
        self.img_label.config(image="")
        self.details_label.config(text="")
        self.status_var.set("Completed")
        self.rating_var.set("0")
        
        title = self.all_anime[self.current_idx]
        self.search_var.set(title)
        
        self.progress_label.config(text="Progress: " + str(self.current_idx + 1) + "/" + str(len(self.all_anime)))
        self.root.update()
        
        self.manual_search()

    def on_select_anime(self, event):
        idx = self.results_box.curselection()
        if not idx or not self.current_results:
            return
            
        selected_data = self.current_results[idx[0]]
        self.selected_mal_id = str(selected_data["mal_id"])
        self.selected_title = selected_data["title"]
        self.selected_type = selected_data.get("type", "TV")
        self.selected_episodes = str(selected_data.get("episodes") or 0)
        
        info_text = "Title: " + self.selected_title + "\nType: " + self.selected_type + "\nScore: " + str(selected_data.get("score", "N/A"))
        self.details_label.config(text=info_text)
        
        img_url = selected_data.get("images", {}).get("jpg", {}).get("image_url")
        if img_url:
            try:
                img_res = requests.get(img_url, timeout=5)
                img_data = Image.open(io.BytesIO(img_res.content))
                img_data.thumbnail((200, 290))
                self.photo_img = ImageTk.PhotoImage(img_data)
                self.img_label.config(image=self.photo_img)
            except Exception:
                self.img_label.config(image="")

    def go_back(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.process_next_anime()
        else:
            messagebox.showinfo("Info", "This is already the first anime in the batch.")

    def submit_current(self):
        score = self.rating_var.get()
        status = self.status_var.get()
        
        watched_eps = self.selected_episodes if status == "Completed" else "0"
        
        anime_xml = "<anime>\n"
        anime_xml += "<series_animedb_id>" + self.selected_mal_id + "</series_animedb_id>\n"
        anime_xml += "<series_title><![CDATA[" + self.selected_title + "]]></series_title>\n"
        anime_xml += "<series_type>" + self.selected_type + "</series_type>\n"
        anime_xml += "<series_episodes>" + self.selected_episodes + "</series_episodes>\n"
        anime_xml += "<my_id>0</my_id>\n"
        anime_xml += "<my_watched_episodes>" + watched_eps + "</my_watched_episodes>\n"
        anime_xml += "<my_start_date>0000-00-00</my_start_date>\n"
        anime_xml += "<my_finish_date>0000-00-00</my_finish_date>\n"
        anime_xml += "<my_rated></my_rated>\n"
        anime_xml += "<my_score>" + score + "</my_score>\n"
        anime_xml += "<my_storage></my_storage>\n"
        anime_xml += "<my_storage_value>0.00</my_storage_value>\n"
        anime_xml += "<my_status>" + status + "</my_status>\n"
        anime_xml += "<my_comments><![CDATA[]]></my_comments>\n"
        anime_xml += "<my_times_watched>0</my_times_watched>\n"
        anime_xml += "<my_rewatch_value></my_rewatch_value>\n"
        anime_xml += "<my_priority>LOW</my_priority>\n"
        anime_xml += "<my_tags><![CDATA[]]></my_tags>\n"
        anime_xml += "<my_rewatching>0</my_rewatching>\n"
        anime_xml += "<my_rewatching_ep>0</my_rewatching_ep>\n"
        anime_xml += "<my_discuss>1</my_discuss>\n"
        anime_xml += "<my_sns>default</my_sns>\n"
        anime_xml += "<update_on_import>1</update_on_import>\n"
        anime_xml += "</anime>\n"
        
        self.anime_xml_dict[self.current_idx] = anime_xml
        
        self.current_idx += 1
        time.sleep(0.4)
        self.process_next_anime()

    def skip_current(self):
        if self.current_idx in self.anime_xml_dict:
            del self.anime_xml_dict[self.current_idx]
        self.current_idx += 1
        self.process_next_anime()

    def save_xml_output(self):
        xml_str = '<?xml version="1.0" encoding="UTF-8" ?>\n'
        xml_str += '<myanimelist>\n'
        xml_str += '<myinfo>\n'
        xml_str += '<user_id>16505659</user_id>\n'
        xml_str += '<user_name>Av1dz</user_name>\n'
        xml_str += '<user_export_type>1</user_export_type>\n'
        xml_str += '</myinfo>\n'
        
        xml_entries = [self.anime_xml_dict[k] for k in sorted(self.anime_xml_dict.keys())]
        xml_str += "".join(xml_entries)
        
        xml_str += '</myanimelist>'
        
        base_name = os.path.basename(self.filename)
        output_filename = "mal_" + base_name.replace(".txt", ".xml")
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(xml_str)
            
        messagebox.showinfo("Success", "Batch processing complete! XML output saved to " + output_filename)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MalGuiImporter(root)
    root.mainloop()