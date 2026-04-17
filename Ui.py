from customtkinter import *
from tkinter import messagebox
import socketio
import threading

# -----------------------------
# Socket.IO client setup
# -----------------------------
sio = socketio.Client()


SERVER_IP = "your ip address" 
SERVER_URL = f"http://{SERVER_IP}:5000"

# -----------------------------
# Main Chat App
# -----------------------------
class MessageApp:
    def __init__(self):
        self.role = None  # attacker or bystander

        self.app = CTk()
        self.app.geometry("500x700")
        self.app.title("Message App")
        self.app.configure(fg_color="#ffffff")

        self.show_role_selector()

    # -----------------------------
    # First Screen: Role selection
    # -----------------------------
    def show_role_selector(self):
        self.selector_frame = CTkFrame(self.app)
        self.selector_frame.pack(expand=True)

        label = CTkLabel(self.selector_frame, text="Choose Your Role", font=("Arial", 24))
        label.pack(pady=20)

        attacker_btn = CTkButton(self.selector_frame, text="Attacker", width=200,
                                 command=lambda: self.select_role("Attacker"))
        attacker_btn.pack(pady=10)

        bystander_btn = CTkButton(self.selector_frame, text="Bystander", width=200,
                                  command=lambda: self.select_role("Bystander"))
        bystander_btn.pack(pady=10)

    def select_role(self, role):
        self.role = role
        self.selector_frame.pack_forget()
        self.build_chat_ui()
        self.start_socket_connection()

    # -----------------------------
    # Chat UI
    # -----------------------------
    def build_chat_ui(self):
        # Chat scroll area
        self.chat_frame = CTkScrollableFrame(self.app, width=460, height=550)
        self.chat_frame.pack(pady=10)

        # Input area frame
        self.input_frame = CTkFrame(self.app, fg_color="#ffffff")
        self.input_frame.pack(fill="x", padx=10, pady=10)

        # Message input
        self.message_input = CTkTextbox(self.input_frame, width=380, height=40,
                                        fg_color="#f0f0f0",
                                        border_width=2, corner_radius=20, text_color="blue")
        self.message_input.pack(side="left", padx=5)

        # Send button
        send_btn = CTkButton(self.input_frame, text="Send", width=70,
                             command=self.send_message, corner_radius=20)
        send_btn.pack(side="right", padx=5)

    # -----------------------------
    # Socket.IO Listeners
    # -----------------------------
    def start_socket_connection(self):
        def connect_thread():
            try:
                sio.connect(SERVER_URL)
                print("Connected to server")
            except Exception as e:
                print("Connection error:", e)
                messagebox.showerror("Error", "Could not connect to server.")

        threading.Thread(target=connect_thread, daemon=True).start()

    # Receive message event
    @sio.on("receive_message")
    def receive_message(data):
        app.display_message(
            username=data["username"],
            text=data["message"],
            is_spam=data["is_spam"],
            confidence=data["confidence"]
        )

    # -----------------------------
    # Send message to server
    # -----------------------------
    def send_message(self):
        text = self.message_input.get("1.0", "end-1c").strip()
        if not text:
            return

        payload = {
            "username": self.role,
            "message": text
        }

        sio.emit("send_message", payload)
        self.message_input.delete("1.0", "end")

    # -----------------------------
    # Display message in UI
    # -----------------------------
    def display_message(self, username, text, is_spam, confidence):
        is_me = (username == self.role)

        # Bubble container
        bubble = CTkFrame(self.chat_frame, fg_color="transparent")

        # ----------------------
        # COLOR LOGIC
        # ----------------------
        if self.role == "Attacker":
            # Attacker always sees blue bubbles
            color = "#007AFF"
        else:
            # Bystander sees spam detection colors
            color = "#FF5C5C" if is_spam else "#007AFF"

        msg_frame = CTkFrame(bubble, fg_color=color, corner_radius=15)
        msg_label = CTkLabel(
            msg_frame,
            text=f"{username}: {text}",
            text_color="white",
            wraplength=300
        )
        msg_label.pack(padx=10, pady=5)
        msg_frame.pack()

        # ----------------------
        # ONLY Bystander sees spam warning
        # ----------------------
        if is_spam and self.role == "Bystander":
            warn = CTkLabel(
                bubble,
                text=f"(⚠️ Spam — {confidence:.2f}% confidence)",
                text_color="#FF0000",
                font=("Arial", 11)
            )
            warn.pack(pady=2)

        # alignment
        anchor = "e" if is_me else "w"
        bubble.pack(anchor=anchor, padx=10, pady=5)


    def run(self):
        self.app.mainloop()


# -----------------------------
# Launch App
# -----------------------------
if __name__ == "__main__":
    app = MessageApp()
    app.run()
