import wx
import database as db
import main_app

# --- COLORS ---
COLOR_BG = '#F5F7FA'
COLOR_CARD = '#FFFFFF'
COLOR_ACCENT = '#1565C0'
COLOR_TEXT = '#2C3E50'

class LoginFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Financify", size=(600, 800))
        self.SetMinSize((500, 700))
        self.Center()
        self.SetBackgroundColour(COLOR_BG)
        # Open maximized to ensure nothing is hidden on small screens
        self.Maximize() 
        self.InitUI()

    def InitUI(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddStretchSpacer(1) 

        # --- CARD PANEL ---
        card = wx.Panel(self)
        card.SetBackgroundColour(COLOR_CARD)
        
        card_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 1. HEADER - Reduced Font Size to fit "Financify"
        title = wx.StaticText(card, label="Welcome to Financify")
        title.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title.SetForegroundColour(COLOR_ACCENT)
        card_sizer.Add(title, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 40)
        
        # 2. INPUTS
        self.user_input = self.create_input_field(card, card_sizer, "Username")
        card_sizer.AddSpacer(20)
        
        self.pass_input = self.create_input_field(card, card_sizer, "Password", is_password=True)
        
        # Forgot Password Link
        card_sizer.AddSpacer(15) 
        self.lbl_forgot = wx.StaticText(card, label="Forgot Password?")
        self.lbl_forgot.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.lbl_forgot.SetForegroundColour(COLOR_ACCENT)
        self.lbl_forgot.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.lbl_forgot.Bind(wx.EVT_LEFT_DOWN, self.OnForgot)
        card_sizer.Add(self.lbl_forgot, 0, wx.ALIGN_RIGHT | wx.RIGHT, 50)

        card_sizer.AddSpacer(40)

        # 3. BUTTONS
        self.btn_login = wx.Button(card, label="Login", size=(-1, 55))
        self.btn_login.SetBackgroundColour(COLOR_ACCENT)
        self.btn_login.SetForegroundColour('WHITE')
        self.btn_login.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        card_sizer.Add(self.btn_login, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 50)
        
        card_sizer.AddSpacer(20)

        self.btn_register = wx.Button(card, label="Create New Account", size=(-1, 55))
        self.btn_register.SetBackgroundColour(COLOR_BG) 
        self.btn_register.SetForegroundColour(COLOR_TEXT)
        self.btn_register.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        card_sizer.Add(self.btn_register, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 50)

        card_sizer.AddSpacer(50) 

        card.SetSizer(card_sizer)
        
        main_sizer.Add(card, 0, wx.EXPAND | wx.ALL, 50)
        main_sizer.AddStretchSpacer(1)

        self.SetSizer(main_sizer)

        self.btn_login.Bind(wx.EVT_BUTTON, self.OnLogin)
        self.btn_register.Bind(wx.EVT_BUTTON, self.OnRegister)
        self.user_input.Bind(wx.EVT_TEXT_ENTER, self.OnLogin)
        self.pass_input.Bind(wx.EVT_TEXT_ENTER, self.OnLogin)

    def create_input_field(self, parent, sizer, label_text, is_password=False):
        lbl = wx.StaticText(parent, label=label_text)
        lbl.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl.SetForegroundColour(COLOR_TEXT)
        sizer.Add(lbl, 0, wx.LEFT | wx.BOTTOM, 50)
        
        style = wx.TE_PASSWORD | wx.TE_PROCESS_ENTER if is_password else wx.TE_PROCESS_ENTER
        txt_ctrl = wx.TextCtrl(parent, size=(-1, 50), style=style)
        sizer.Add(txt_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 50)
        return txt_ctrl

    def OnLogin(self, e):
        username = self.user_input.GetValue().strip()
        password = self.pass_input.GetValue()
        success, message, user_id = db.login_user(username, password)
        
        if success:
            db.check_and_create_default_account(user_id)
            self.Close()
            main_app.MainFrame(user_id).Show()
        else:
            wx.MessageBox(message, "Login Failed", wx.OK | wx.ICON_ERROR)

    def OnRegister(self, e):
        dlg = RegistrationDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            user, pwd, sec = dlg.GetValues()
            success, message = db.register_user(user, pwd, sec)
            if success:
                wx.MessageBox("Account created successfully! You can now Login.", "Success", wx.ICON_INFORMATION)
            else:
                wx.MessageBox(message, "Registration Error", wx.ICON_ERROR)
        dlg.Destroy()

    def OnForgot(self, e):
        dlg_u = wx.TextEntryDialog(self, "Enter your Username:", "Recovery")
        if dlg_u.ShowModal() != wx.ID_OK: return
        user = dlg_u.GetValue()
        dlg_u.Destroy()

        if not user: return

        dlg_s = wx.TextEntryDialog(self, f"Hello {user}.\n\nFavorite Food?", "Security Check")
        if dlg_s.ShowModal() != wx.ID_OK: return
        ans = dlg_s.GetValue()
        dlg_s.Destroy()

        if db.verify_security_answer(user, ans):
            dlg_p = wx.TextEntryDialog(self, "Identity Verified!\nEnter New Password:", "Reset Password")
            if dlg_p.ShowModal() == wx.ID_OK:
                new_pass = dlg_p.GetValue()
                if len(new_pass) >= 4:
                    if db.reset_password(user, new_pass):
                        wx.MessageBox("Password reset! Please Login.", "Success")
                    else:
                        wx.MessageBox("Database Error.", "Error")
                else:
                    wx.MessageBox("Password too short.", "Error")
            dlg_p.Destroy()
        else:
            wx.MessageBox("Incorrect Username or Security Answer.", "Access Denied", wx.OK | wx.ICON_ERROR)

class RegistrationDialog(wx.Dialog):
    def __init__(self, parent):
        # We DO NOT use a Panel inside the Dialog to avoid the Parent/Sizer crash
        # We add everything directly to the Dialog (self)
        super().__init__(parent, title="Create Account", size=(400, 550))
        self.Center()
        
        v = wx.BoxSizer(wx.VERTICAL)
        
        v.Add(wx.StaticText(self, label="Username"), 0, wx.TOP|wx.LEFT, 20)
        self.u = wx.TextCtrl(self, size=(-1, 40))
        v.Add(self.u, 0, wx.EXPAND|wx.ALL, 20)
        
        v.Add(wx.StaticText(self, label="Password"), 0, wx.TOP|wx.LEFT, 5)
        self.p = wx.TextCtrl(self, size=(-1, 40), style=wx.TE_PASSWORD)
        v.Add(self.p, 0, wx.EXPAND|wx.ALL, 20)
        
        v.Add(wx.StaticText(self, label="Security: Favorite Food?"), 0, wx.TOP|wx.LEFT, 5)
        self.s = wx.TextCtrl(self, size=(-1, 40))
        v.Add(self.s, 0, wx.EXPAND|wx.ALL, 20)
        
        # Safe way to create buttons: Manual sizer
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(self, wx.ID_OK, "Create Account")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(ok_btn, 1, wx.RIGHT, 10)
        btn_sizer.Add(cancel_btn, 1)
        
        v.Add(btn_sizer, 0, wx.EXPAND|wx.ALL, 20)
        
        self.SetSizer(v)

    def GetValues(self):
        return self.u.GetValue(), self.p.GetValue(), self.s.GetValue()

if __name__ == '__main__':
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except: pass

    db.initialize_database()
    app = wx.App(False)
    frame = LoginFrame()
    frame.Show()
    app.MainLoop()
