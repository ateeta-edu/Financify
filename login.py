import wx
import database as db
import main_app

# AESTHETIC LIGHT THEME
BG_COLOR = '#F5F7FA'
TEXT_COLOR = '#2C3E50'
ACCENT_COLOR = '#1565C0' # Royal Blue

class LoginFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Financify", size=(600, 500))
        self.Center()
        self.SetBackgroundColour(BG_COLOR)
        self.InitUI()

    def InitUI(self):
        p = wx.Panel(self)
        p.SetBackgroundColour(BG_COLOR)
        
        main_v = wx.BoxSizer(wx.VERTICAL)
        main_v.AddStretchSpacer(1) 
        
        t = wx.StaticText(p, label="Financify")
        t.SetFont(wx.Font(36, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        t.SetForegroundColour(ACCENT_COLOR)
        main_v.Add(t, 0, wx.ALIGN_CENTER | wx.BOTTOM, 40)

        form_v = wx.BoxSizer(wx.VERTICAL)
        
        l1 = wx.StaticText(p, label="Username")
        l1.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        l1.SetForegroundColour(TEXT_COLOR)
        form_v.Add(l1, 0, wx.BOTTOM, 5)
        
        self.u = wx.TextCtrl(p, size=(280, 35), style=wx.TE_PROCESS_ENTER)
        form_v.Add(self.u, 0, wx.BOTTOM, 20)
        
        l2 = wx.StaticText(p, label="Password")
        l2.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        l2.SetForegroundColour(TEXT_COLOR)
        form_v.Add(l2, 0, wx.BOTTOM, 5)
        
        self.p = wx.TextCtrl(p, size=(280, 35), style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        form_v.Add(self.p, 0, wx.BOTTOM, 30)
        
        h = wx.BoxSizer(wx.HORIZONTAL)
        b1 = wx.Button(p, label="Login", size=(130, 40))
        b1.SetBackgroundColour(ACCENT_COLOR)
        b1.SetForegroundColour('white')
        
        b2 = wx.Button(p, label="Register", size=(130, 40))
        b2.SetBackgroundColour('white')
        b2.SetForegroundColour(ACCENT_COLOR)
        
        h.Add(b1, 0, wx.RIGHT, 15)
        h.Add(b2, 0)
        
        form_v.Add(h, 0, wx.ALIGN_CENTER)
        main_v.Add(form_v, 0, wx.ALIGN_CENTER)
        main_v.AddStretchSpacer(1) 

        p.SetSizer(main_v)
        
        b1.Bind(wx.EVT_BUTTON, self.OnLog)
        b2.Bind(wx.EVT_BUTTON, self.OnReg)
        self.u.Bind(wx.EVT_TEXT_ENTER, self.OnLog)
        self.p.Bind(wx.EVT_TEXT_ENTER, self.OnLog)

    def OnLog(self, e):
        s, m, uid = db.login_user(self.u.GetValue(), self.p.GetValue())
        if s:
            db.check_and_create_default_account(uid)
            self.Close()
            main_app.MainFrame(uid).Show()
        else: wx.MessageBox(m, "Error")

    def OnReg(self, e):
        s, m = db.register_user(self.u.GetValue(), self.p.GetValue())
        if s: 
            wx.MessageBox("Registered!", "Success")
            self.u.SetValue("")
            self.p.SetValue("")
        else: wx.MessageBox(m, "Error")

if __name__ == '__main__':
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except: pass

    db.initialize_database()
    app = wx.App(False)
    LoginFrame().Show()
    app.MainLoop()