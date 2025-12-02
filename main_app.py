import wx
import wx.adv 
import database as db
from datetime import datetime
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import random
import csv 
import os
import webbrowser

# --- OFFLINE TIP/QUOTE LIST ---
TIPS_AND_QUOTES = [
    "A budget is telling your money where to go, instead of wondering where it went.",
    "Do not save what is left after spending; instead, spend what is left after saving.",
    "Try the '50/30/20' rule: 50% for needs, 30% for wants, 20% for savings.",
    "Review your subscriptions. Are you still using all of them?",
    "Set a 'no-spend' day once a week. You might be surprised how much you save!",
    "Always make a shopping list before you go to the grocery store.",
    "Brew your coffee at home. It adds up!",
    "Wait 24 hours before making any large, non-essential purchase.",
    "The art is not in making money, but in keeping it.",
    "Pay yourself first: Automatically transfer money to savings on payday.",
    "Financial freedom is the only road to history.",
    "Beware of little expenses. A small leak will sink a great ship.",
    "It's not your salary that makes you rich, it's your spending habits.",
    "The quickest way to double your money is to fold it over and put it back in your pocket.",
    "If you buy things you do not need, soon you will have to sell things you do need."
]

CATEGORIES = ['Food', 'Transport', 'Rent', 'Utilities', 'Salary', 'Entertainment', 'Shopping', 'Health', 'Education', 'Groceries', 'Other']

# --- COLORS ---
COLOR_WHITE = '#FFFFFF'
COLOR_LIGHT_GRAY = '#F5F5F5'
COLOR_DARK_GRAY = '#333333'
COLOR_GREEN = '#4CAF50'
COLOR_RED = '#E74C3C'
COLOR_BLUE = '#008CBA'
COLOR_PURPLE = '#9B59B6'
COLOR_ORANGE = '#F39C12'
# Added missing color definition just in case
CARD_COLOR = '#FFFFFF' 

def smart_date_parse(date_str):
    formats = ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%y']
    for fmt in formats:
        try: return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError: pass
    return datetime.now().strftime('%Y-%m-%d')

class MainFrame(wx.Frame):
    def __init__(self, user_id):
        super().__init__(None, title="Financify", size=(1200, 800)) 
        self.user_id = user_id
        self.SetMinSize((1000, 700))
        self.SetBackgroundColour(COLOR_WHITE)
        self.Center()
        self.Maximize()
        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)
        panel.SetBackgroundColour(COLOR_WHITE)
        
        self.notebook = wx.Notebook(panel)
        self.notebook.SetBackgroundColour(COLOR_WHITE)
        
        self.dashboard_panel = DashboardPanel(self.notebook, self.user_id)
        self.notebook.AddPage(self.dashboard_panel, "Dashboard")

        self.reports_panel = ReportsPanel(self.notebook, self.user_id)
        self.notebook.AddPage(self.reports_panel, "Reports & Data")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 10)
        panel.SetSizer(sizer)
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnTabChanged)
        self.dashboard_panel.RefreshData()
        self.Show()

    def OnTabChanged(self, event):
        current_page = self.notebook.GetCurrentPage()
        if hasattr(current_page, "RefreshData"):
            current_page.RefreshData()
        event.Skip()
    
    def RefreshAllTabs(self):
        self.dashboard_panel.RefreshData()
        self.reports_panel.RefreshData()

class DashboardPanel(wx.Panel):
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.user_id = user_id
        self.SetBackgroundColour(COLOR_WHITE)
        self.account_map = {} 
        self.selected_category = None
        self.InitUI()
        self.LoadData()

    def InitUI(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # HEADER
        header_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- STABLE TITLE (Standard Text, No Crash) ---
        title = wx.StaticText(self, label="Financify ✨")
        title.SetFont(wx.Font(32, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title.SetForegroundColour(COLOR_PURPLE)
        
        # Manual Click Logic
        title.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        title.Bind(wx.EVT_LEFT_DOWN, self.OnGetAITip)
        
        header_sizer.Add(title, 0, wx.ALIGN_LEFT | wx.BOTTOM, 5)

        self.quote_text = wx.StaticText(self, label=f"\"{random.choice(TIPS_AND_QUOTES)}\"")
        self.quote_text.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        self.quote_text.SetForegroundColour(COLOR_DARK_GRAY)
        self.quote_text.Wrap(800)
        
        # Quote is also clickable
        self.quote_text.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.quote_text.Bind(wx.EVT_LEFT_DOWN, self.OnGetAITip)

        tip_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tip_sizer.Add(self.quote_text, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # Optional button if user prefers clicking a button
        tip_btn = wx.Button(self, label="Get New Tip", size=(100, -1))
        tip_btn.Bind(wx.EVT_BUTTON, self.OnGetAITip)
        tip_sizer.Add(tip_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        header_sizer.Add(tip_sizer, 0, wx.EXPAND | wx.BOTTOM, 20)
        main_sizer.Add(header_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 20)

        # CONTENT
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Left Col
        left_col = wx.BoxSizer(wx.VERTICAL)
        self.transaction_form = self.CreateTransactionForm(self)
        left_col.Add(self.transaction_form, 0, wx.EXPAND | wx.BOTTOM, 15)
        self.category_budget_panel = self.CreateCategoryBudgetsPanel(self)
        left_col.Add(self.category_budget_panel, 1, wx.EXPAND)
        content_sizer.Add(left_col, 1, wx.EXPAND | wx.RIGHT, 15)

        # Right Col
        right_col = wx.BoxSizer(wx.VERTICAL)
        self.key_numbers_panel = self.CreateKeyNumbersPanel(self)
        right_col.Add(self.key_numbers_panel, 0, wx.EXPAND | wx.BOTTOM, 15)
        self.pie_chart_panel = self.CreatePieChartPanel(self)
        right_col.Add(self.pie_chart_panel, 1, wx.EXPAND)
        content_sizer.Add(right_col, 1, wx.EXPAND)
        
        main_sizer.Add(content_sizer, 1, wx.EXPAND | wx.ALL, 20)
        self.SetSizer(main_sizer)

    def OnGetAITip(self, event):
        """Picks a random tip from the list."""
        tip = random.choice(TIPS_AND_QUOTES)
        self.quote_text.SetLabel(f"\"{tip}\"")
        self.quote_text.Wrap(800)
        self.Layout()

    def CreateTransactionForm(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(COLOR_LIGHT_GRAY)
        header = wx.Panel(panel)
        header.SetBackgroundColour(COLOR_WHITE)
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl = wx.StaticText(header, label=" Add Transaction")
        lbl.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl.SetForegroundColour(COLOR_DARK_GRAY)
        h_sizer.Add(lbl, 1, wx.ALL, 8)
        header.SetSizer(h_sizer)
        
        main_v = wx.BoxSizer(wx.VERTICAL)
        main_v.Add(header, 0, wx.EXPAND | wx.BOTTOM, 10)
        
        grid = wx.FlexGridSizer(6, 2, 10, 10)
        self.date_picker = wx.adv.DatePickerCtrl(panel, style=wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY)
        min_date = wx.DateTime(1, wx.DateTime.Jan, 2025)
        self.date_picker.SetRange(min_date, wx.DefaultDateTime)
        self.date_picker.SetValue(wx.DateTime.Now())

        self.type_choice = wx.Choice(panel, choices=['Expense', 'Income'])
        self.type_choice.SetSelection(0)
        self.amount_ctrl = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.category_choice = wx.ComboBox(panel, choices=CATEGORIES, style=wx.CB_DROPDOWN)
        self.desc_ctrl = wx.TextCtrl(panel, size=(-1, 50), style=wx.TE_MULTILINE) 
        
        def sl(text): 
            t = wx.StaticText(panel, label=text)
            t.SetForegroundColour(COLOR_DARK_GRAY)
            return t

        grid.AddMany([
            (sl("Date:"), 0, wx.ALIGN_CENTER_VERTICAL), (self.date_picker, 1, wx.EXPAND),
            (sl("Type:"), 0, wx.ALIGN_CENTER_VERTICAL), (self.type_choice, 1, wx.EXPAND),
            (sl("Amount:"), 0, wx.ALIGN_CENTER_VERTICAL), (self.amount_ctrl, 1, wx.EXPAND),
            (sl("Category:"), 0, wx.ALIGN_CENTER_VERTICAL), (self.category_choice, 1, wx.EXPAND),
            (sl("Desc:"), 0, wx.ALIGN_TOP), (self.desc_ctrl, 1, wx.EXPAND)
        ])
        grid.AddGrowableCol(1, 1)
        main_v.Add(grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        self.submit_btn = wx.Button(panel, label="Add Transaction", size=(-1, 40))
        self.submit_btn.SetBackgroundColour(COLOR_GREEN)
        self.submit_btn.SetForegroundColour('white')
        self.submit_btn.Bind(wx.EVT_BUTTON, self.OnSubmitTransaction)
        main_v.Add(self.submit_btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        panel.SetSizer(main_v)
        return panel

    def CreateKeyNumbersPanel(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(COLOR_WHITE)
        v = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="This Month")
        lbl.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl.SetForegroundColour(COLOR_DARK_GRAY)
        v.Add(lbl, 0, wx.ALL, 15)
        h = wx.BoxSizer(wx.HORIZONTAL)
        bl = wx.StaticText(panel, label="Budget: ₹")
        bl.SetForegroundColour(COLOR_DARK_GRAY)
        h.Add(bl, 0, wx.ALIGN_CENTER_VERTICAL)
        self.budget_ctrl = wx.TextCtrl(panel, value="0.00")
        h.Add(self.budget_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        b_btn = wx.Button(panel, label="Set", size=(50, -1))
        b_btn.Bind(wx.EVT_BUTTON, self.OnSetBudget)
        h.Add(b_btn, 0)
        v.Add(h, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        self.income_text = wx.StaticText(panel, label="Income: ₹0.00")
        self.spent_text = wx.StaticText(panel, label="Spent: ₹0.00")
        self.remaining_text = wx.StaticText(panel, label="Left: ₹0.00")
        self.net_text = wx.StaticText(panel, label="Savings: ₹0.00")
        for t in [self.income_text, self.spent_text, self.remaining_text, self.net_text]:
            t.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            v.Add(t, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.income_text.SetForegroundColour(COLOR_GREEN)
        self.spent_text.SetForegroundColour(COLOR_RED)
        panel.SetSizer(v)
        return panel
        
    def CreateCategoryBudgetsPanel(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(COLOR_WHITE)
        v = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="Category Budgets")
        lbl.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl.SetForegroundColour(COLOR_DARK_GRAY)
        v.Add(lbl, 0, wx.ALL, 15)
        self.category_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_NO_HEADER)
        self.category_list.InsertColumn(0, "Cat", width=180)
        self.category_list.InsertColumn(1, "Bud", width=120)
        self.category_list.InsertColumn(2, "Spt", width=120)
        self.category_list.InsertColumn(3, "Rem", width=120)
        self.category_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnCategorySelected)
        v.Add(self.category_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        h = wx.BoxSizer(wx.HORIZONTAL)
        self.add_cat_btn = wx.Button(panel, label="Set Budget")
        self.add_cat_btn.Bind(wx.EVT_BUTTON, self.OnAddEditCategory)
        h.Add(self.add_cat_btn, 1, wx.RIGHT, 5)
        self.delete_cat_btn = wx.Button(panel, label="Delete")
        self.delete_cat_btn.Bind(wx.EVT_BUTTON, self.OnDeleteCategory)
        self.delete_cat_btn.Disable()
        h.Add(self.delete_cat_btn, 1, wx.LEFT, 5)
        v.Add(h, 0, wx.EXPAND | wx.ALL, 15)
        panel.SetSizer(v)
        return panel

    def CreatePieChartPanel(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(COLOR_WHITE)
        v = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="Breakdown")
        lbl.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl.SetForegroundColour(COLOR_DARK_GRAY)
        v.Add(lbl, 0, wx.ALL, 15)
        self.pie_figure = Figure(figsize=(3, 2.5)) 
        self.pie_figure.set_facecolor(COLOR_WHITE)
        self.pie_figure.set_tight_layout(True)
        self.pie_axes = self.pie_figure.add_subplot(111) 
        self.pie_canvas = FigureCanvas(panel, -1, self.pie_figure)
        v.Add(self.pie_canvas, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        panel.SetSizer(v)
        return panel

    def LoadData(self):
        accounts = db.get_accounts(self.user_id)
        self.default_account_id = accounts[0]['account_id'] if accounts else None

    def RefreshData(self):
        self.LoadData()
        today = datetime.now()
        month, year = today.month, today.year
        data = db.get_dashboard_numbers(self.user_id, month, year)
        self.budget_ctrl.SetValue(f"{data['budget']:.2f}")
        self.income_text.SetLabel(f"Income: ₹{data['income']:.2f}")
        self.spent_text.SetLabel(f"Spent: ₹{data['spent']:.2f}")
        self.remaining_text.SetLabel(f"Left: ₹{data['remaining']:.2f}")
        self.net_text.SetLabel(f"Savings: ₹{data['net']:.2f}")
        if data['remaining'] < 0: self.remaining_text.SetForegroundColour(COLOR_RED)
        else: self.remaining_text.SetForegroundColour(COLOR_BLUE) 
        if data['net'] < 0: self.net_text.SetForegroundColour(COLOR_RED)
        else: self.net_text.SetForegroundColour(COLOR_GREEN)
        chart_data = db.get_expense_data_for_pie_chart(self.user_id, month, year)
        self.pie_axes.clear()
        if not chart_data:
            self.pie_axes.text(0.5, 0.5, 'No Data', ha='center', va='center')
        else:
            labels = [row['category'] for row in chart_data]
            sizes = [row['total'] for row in chart_data]
            self.pie_axes.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            self.pie_axes.set_title(f'{today.strftime("%B")}')
        self.pie_canvas.draw()
        self.RefreshCategoryBudgets()
        self.Layout()

    def RefreshCategoryBudgets(self):
        self.category_list.DeleteAllItems()
        today = datetime.now()
        cat_budgets = db.get_category_budgets_with_spending(self.user_id, today.month, today.year)
        for index, item in enumerate(cat_budgets):
            remaining = item['budget'] - item['spent']
            self.category_list.InsertItem(index, item['category'])
            self.category_list.SetItem(index, 1, f"₹{item['budget']:.2f}")
            self.category_list.SetItem(index, 2, f"₹{item['spent']:.2f}")
            self.category_list.SetItem(index, 3, f"₹{remaining:.2f}")
            if remaining < 0: self.category_list.SetItemTextColour(index, COLOR_RED)
            else: self.category_list.SetItemTextColour(index, COLOR_BLUE)
        self.selected_category = None
        self.delete_cat_btn.Disable()

    def OnSubmitTransaction(self, event):
        try:
            date_obj = self.date_picker.GetValue()
            date_str = date_obj.FormatISODate()
            trans_type = self.type_choice.GetStringSelection()
            amount = self.amount_ctrl.GetValue()
            category = self.category_choice.GetValue()
            description = self.desc_ctrl.GetValue()

            if not amount: raise ValueError("Enter Amount")
            if float(amount) <= 0: raise ValueError("Amount must be > 0")
            if not category: raise ValueError("Select Category")

            # ALERT
            if trans_type == 'Expense':
                cat_budgets = db.get_category_budgets_with_spending(self.user_id, datetime.now().month, datetime.now().year)
                this_cat = next((item for item in cat_budgets if item['category'] == category), None)
                if this_cat and this_cat['budget'] > 0:
                    if (this_cat['spent'] + float(amount)) > this_cat['budget']:
                         wx.MessageBox(f"⚠️ Alert: Exceeding {category} Budget!", "Warning", wx.OK|wx.ICON_WARNING)

            success, message, _ = db.add_transaction(self.user_id, self.default_account_id, date_str, amount, trans_type, category, description, tags="")
            if not success: raise Exception(message)
            wx.MessageBox("Added!", "Success", wx.OK | wx.ICON_INFORMATION)
            self.ClearForm()
            wx.GetApp().GetTopWindow().RefreshAllTabs()
        except Exception as e: wx.MessageBox(f"Error: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def ClearForm(self):
        self.date_picker.SetValue(wx.DateTime.Now())
        self.type_choice.SetSelection(0)
        self.amount_ctrl.SetValue("")
        self.category_choice.SetValue("")
        self.desc_ctrl.SetValue("")

    def OnSetBudget(self, event):
        try:
            amount = float(self.budget_ctrl.GetValue())
            if amount < 0: raise ValueError("Negative Budget")
            db.set_monthly_budget(self.user_id, datetime.now().month, datetime.now().year, amount)
            self.RefreshData()
        except: pass

    def OnCategorySelected(self, event):
        self.selected_category = self.category_list.GetItemText(event.GetIndex(), 0)
        self.delete_cat_btn.Enable()
    
    def OnAddEditCategory(self, event):
        today = datetime.now()
        all_cats = set(CATEGORIES)
        budgets = {item['category'] for item in db.get_category_budgets_with_spending(self.user_id, today.month, today.year)}
        available_cats = [c for c in all_cats if c not in budgets and c != 'Salary']
        dlg = CategoryBudgetDialog(self, available_cats)
        if dlg.ShowModal() == wx.ID_OK:
            c, a = dlg.GetValues()
            if c and a > 0:
                db.set_category_budget(self.user_id, c, a, today.month, today.year)
                self.RefreshData()
        dlg.Destroy()
    
    def OnDeleteCategory(self, event):
        if not self.selected_category: return
        if wx.MessageBox(f"Delete budget for {self.selected_category}?", "Confirm", wx.YES_NO) == wx.YES:
            db.delete_category_budget(self.user_id, self.selected_category, datetime.now().month, datetime.now().year)
            self.RefreshData()

class ReportsPanel(wx.Panel):
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.user_id = user_id
        self.SetBackgroundColour(COLOR_WHITE)
        self.InitUI()

    def InitUI(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.bar_chart_panel = self.CreateBarChartPanel(self)
        main_sizer.Add(self.bar_chart_panel, 1, wx.EXPAND | wx.ALL, 10)

        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.search_ctrl = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.search_ctrl.SetDescriptiveText("Search...")
        self.search_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.search_ctrl.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        toolbar_sizer.Add(self.search_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        self.import_btn = wx.Button(self, label="Import CSV")
        self.import_btn.Bind(wx.EVT_BUTTON, self.OnImportCSV)
        toolbar_sizer.Add(self.import_btn, 0, wx.ALL, 5)
        self.export_btn = wx.Button(self, label="Export CSV")
        self.export_btn.Bind(wx.EVT_BUTTON, self.OnExportCSV)
        toolbar_sizer.Add(self.export_btn, 0, wx.ALL, 5)
        self.report_btn = wx.Button(self, label="Generate Report")
        self.report_btn.Bind(wx.EVT_BUTTON, self.OnGenerateReport)
        toolbar_sizer.Add(self.report_btn, 0, wx.ALL, 5)
        self.reset_btn = wx.Button(self, label="Reset All Data")
        self.reset_btn.SetForegroundColour(COLOR_RED)
        self.reset_btn.Bind(wx.EVT_BUTTON, self.OnReset)
        toolbar_sizer.Add(self.reset_btn, 0, wx.ALL, 5)
        main_sizer.Add(toolbar_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        self.trans_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES)
        self.trans_list.InsertColumn(0, "ID", width=0)
        self.trans_list.InsertColumn(1, "Date", width=120)
        self.trans_list.InsertColumn(2, "Type", width=100)
        self.trans_list.InsertColumn(3, "Amount", width=120, format=wx.LIST_FORMAT_RIGHT)
        self.trans_list.InsertColumn(4, "Category", width=150)
        self.trans_list.InsertColumn(5, "Account", width=0)
        self.trans_list.InsertColumn(6, "Description", width=300)
        main_sizer.Add(self.trans_list, 2, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(main_sizer)
        self.trans_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickTransaction)
        self.selected_trans_id = None

    def CreateBarChartPanel(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(CARD_COLOR)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.bar_figure = Figure(figsize=(5, 2.5)) 
        self.bar_figure.set_facecolor(CARD_COLOR)
        self.bar_axes = self.bar_figure.add_subplot(111) 
        self.bar_canvas = FigureCanvas(panel, -1, self.bar_figure)
        sizer.Add(self.bar_canvas, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        return panel

    def RefreshData(self, search_term=""):
        bar_data = db.get_monthly_comparison_data(self.user_id)
        self.bar_axes.clear()
        if not bar_data: self.bar_axes.text(0.5, 0.5, 'No Data', ha='center')
        else:
            import numpy as np
            months = [r['month'] for r in bar_data]
            income = [r['income'] for r in bar_data]
            expense = [r['expense'] for r in bar_data]
            x = np.arange(len(months))
            width = 0.35
            self.bar_axes.bar(x - width/2, income, width, label='Income', color=COLOR_GREEN)
            self.bar_axes.bar(x + width/2, expense, width, label='Expense', color=COLOR_RED)
            self.bar_axes.set_ylabel('Amount (₹)')
            self.bar_axes.set_title('Income vs Expenses')
            self.bar_axes.set_xticks(x)
            self.bar_axes.set_xticklabels(months)
            self.bar_axes.legend()
            self.bar_figure.autofmt_xdate()
        self.bar_canvas.draw()
        self.trans_list.DeleteAllItems()
        rows = db.get_transactions_by_filter(self.user_id, search_term)
        for i, r in enumerate(rows):
            self.trans_list.InsertItem(i, str(r['transaction_id']))
            self.trans_list.SetItem(i, 1, r['date'])
            self.trans_list.SetItem(i, 2, r['type'])
            v = f"₹{r['amount']}" if r['type']=='Expense' else f"+₹{r['amount']}"
            self.trans_list.SetItem(i, 3, v)
            self.trans_list.SetItem(i, 4, r['category'])
            self.trans_list.SetItem(i, 5, r['account_name'])
            self.trans_list.SetItem(i, 6, r['description'])
            if r['type'] == 'Income': self.trans_list.SetItemTextColour(i, COLOR_GREEN)
            else: self.trans_list.SetItemTextColour(i, COLOR_RED)
    
    def OnSearch(self, event): self.RefreshData(self.search_ctrl.GetValue())

    def OnRightClickTransaction(self, event):
        self.selected_trans_id = int(self.trans_list.GetItemText(event.GetIndex(), 0))
        menu = wx.Menu()
        menu.Append(1, "Edit")
        menu.Append(2, "Delete")
        menu.Append(3, "Clone")
        self.Bind(wx.EVT_MENU, self.OnEdit, id=1)
        self.Bind(wx.EVT_MENU, self.OnDelete, id=2)
        self.Bind(wx.EVT_MENU, self.OnClone, id=3)
        self.PopupMenu(menu)
        menu.Destroy()

    def OnClone(self, event):
        trans = [t for t in db.get_transactions_by_filter(self.user_id) if t['transaction_id'] == self.selected_trans_id][0]
        db.add_transaction(self.user_id, trans['account_id'], datetime.now().strftime('%Y-%m-%d'), 
                           abs(trans['amount']), trans['type'], trans['category'], trans['description'] + " (Clone)", "")
        wx.GetApp().GetTopWindow().RefreshAllTabs()
        wx.MessageBox("Cloned!", "Success")

    def OnEdit(self, event):
        trans = [t for t in db.get_transactions_by_filter(self.user_id) if t['transaction_id'] == self.selected_trans_id]
        if not trans: return
        dlg = TransactionEditDialog(self, self.user_id, trans[0], db.get_accounts(self.user_id))
        if dlg.ShowModal() == wx.ID_OK: wx.GetApp().GetTopWindow().RefreshAllTabs()
        dlg.Destroy()

    def OnDelete(self, event):
        if wx.MessageBox("Delete?", "Confirm", wx.YES_NO) == wx.YES:
            db.delete_transaction(self.selected_trans_id, self.user_id)
            wx.GetApp().GetTopWindow().RefreshAllTabs()

    def OnGenerateReport(self, event):
        path = os.path.abspath("report.html")
        rows = db.get_transactions_by_filter(self.user_id)
        html = "<html><body><h1>Financify Report</h1><table border='1'><tr><th>Date</th><th>Type</th><th>Amount</th><th>Category</th><th>Desc</th></tr>"
        for r in rows:
            c = "green" if r['type']=='Income' else "red"
            html += f"<tr><td>{r['date']}</td><td>{r['type']}</td><td style='color:{c}'>{r['amount']}</td><td>{r['category']}</td><td>{r['description']}</td></tr>"
        html += "</table></body></html>"
        with open(path, "w") as f: f.write(html)
        webbrowser.open('file://' + path)

    def OnExportCSV(self, event):
        with wx.FileDialog(self, "Save", wildcard="*.csv", style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL: return
            try:
                rows = db.get_transactions_by_filter(self.user_id)
                with open(dlg.GetPath(), 'w', newline='', encoding='utf-8') as f:
                    w = csv.DictWriter(f, fieldnames=rows[0].keys())
                    w.writeheader()
                    for r in rows: w.writerow(dict(r))
                wx.MessageBox("Exported!")
            except Exception as e: wx.MessageBox(str(e))

    def OnImportCSV(self, event):
        with wx.FileDialog(self, "Open", wildcard="*.csv", style=wx.FD_OPEN) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL: return
            try:
                acc = db.get_accounts(self.user_id)[0]['account_id']
                conn = db.get_db_connection()
                conn.execute('BEGIN')
                with open(dlg.GetPath(), 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    reader.fieldnames = [name.lower().strip() for name in reader.fieldnames]
                    for r in reader:
                        d_str = smart_date_parse(r['date'])
                        if not db.check_transaction_exists(self.user_id, d_str, abs(float(r['amount'])), r.get('description',''), conn):
                            t_type = r.get('type', 'Expense').capitalize()
                            if t_type not in ['Income', 'Expense']: t_type = 'Expense'
                            db.add_transaction(self.user_id, acc, d_str, abs(float(r['amount'])), 
                                               t_type, r.get('category','Other'), r.get('description', ''), "", conn)
                conn.commit()
                conn.close()
                wx.MessageBox("Imported!")
                wx.GetApp().GetTopWindow().RefreshAllTabs()
            except Exception as e: wx.MessageBox(str(e))

    def OnReset(self, event):
        if wx.MessageBox("Are you sure? This wipes EVERYTHING.", "RESET", wx.YES_NO|wx.ICON_ERROR) == wx.YES:
            db.wipe_user_data(self.user_id)
            wx.GetApp().GetTopWindow().RefreshAllTabs()
            wx.MessageBox("All data has been wiped.", "Reset Complete")

class CategoryBudgetDialog(wx.Dialog):
    def __init__(self, parent, available_categories):
        super().__init__(parent, title="Budget", size=(400, 300))
        p = wx.Panel(self)
        v = wx.BoxSizer(wx.VERTICAL)
        self.ch = wx.Choice(p, choices=available_categories)
        self.amt = wx.TextCtrl(p)
        v.Add(wx.StaticText(p, label="Category"), 0, wx.ALL, 5)
        v.Add(self.ch, 0, wx.EXPAND|wx.ALL, 5)
        v.Add(wx.StaticText(p, label="Amount"), 0, wx.ALL, 5)
        v.Add(self.amt, 0, wx.EXPAND|wx.ALL, 5)
        b = wx.StdDialogButtonSizer()
        b.AddButton(wx.Button(p, wx.ID_OK))
        b.AddButton(wx.Button(p, wx.ID_CANCEL))
        b.Realize()
        v.Add(b, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        p.SetSizer(v)
    def GetValues(self): return self.ch.GetStringSelection(), float(self.amt.GetValue())

class TransactionEditDialog(wx.Dialog):
    def __init__(self, parent, user_id, t, accounts):
        super().__init__(parent, title="Edit", size=(400, 400))
        self.user_id, self.t, self.accs, self.amap = user_id, t, accounts, {}
        p = wx.Panel(self)
        v = wx.BoxSizer(wx.VERTICAL)
        self.date = wx.adv.DatePickerCtrl(p)
        self.type = wx.Choice(p, choices=['Expense', 'Income'])
        self.amt = wx.TextCtrl(p)
        self.cat = wx.ComboBox(p, choices=CATEGORIES)
        self.desc = wx.TextCtrl(p)
        
        for l, c in [("Date", self.date), ("Type", self.type), ("Amount", self.amt), ("Category", self.cat), ("Desc", self.desc)]:
            v.Add(wx.StaticText(p, label=l), 0, wx.TOP|wx.LEFT, 5)
            v.Add(c, 0, wx.EXPAND|wx.ALL, 5)
            
        self.LoadData()
        
        b = wx.StdDialogButtonSizer()
        save = wx.Button(p, wx.ID_OK, "Save")
        b.AddButton(save)
        b.AddButton(wx.Button(p, wx.ID_CANCEL))
        b.Realize()
        v.Add(b, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        p.SetSizer(v)
        save.Bind(wx.EVT_BUTTON, self.OnSave)

    def LoadData(self):
        for a in self.accs: self.amap[a['account_name']] = a['account_id']
        dt = datetime.strptime(self.t['date'], '%Y-%m-%d')
        wxdt = wx.DateTime(dt.day, dt.month-1, dt.year)
        self.date.SetValue(wxdt)
        self.type.SetStringSelection(self.t['type'])
        self.amt.SetValue(str(abs(self.t['amount'])))
        self.cat.SetValue(self.t['category'])
        self.desc.SetValue(self.t['description'])

    def OnSave(self, e):
        try:
            v = float(self.amt.GetValue())
            if v <= 0: raise ValueError
            acc_id = list(self.amap.values())[0]
            nd = {'date': self.date.GetValue().FormatISODate(), 'type': self.type.GetStringSelection(), 'amount': v,
                  'account_id': acc_id, 'category': self.cat.GetValue(), 'description': self.desc.GetValue()}
            db.update_transaction(self.t['transaction_id'], self.user_id, nd)
            self.EndModal(wx.ID_OK)
        except: wx.MessageBox("Error")

def smart_date_parse(date_str):
    formats = ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%y']
    for fmt in formats:
        try: return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError: pass
    return datetime.now().strftime('%Y-%m-%d')
