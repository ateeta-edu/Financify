import wx
import wx.adv 
import database as db
from datetime import datetime
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import csv 
import os
import webbrowser

CATEGORIES = ['Food', 'Transport', 'Rent', 'Utilities', 'Salary', 'Entertainment', 'Shopping', 'Health', 'Education', 'Groceries', 'Other']

COLOR_WHITE = '#FFFFFF'
COLOR_BG = '#F5F7FA'
COLOR_TEXT_MAIN = '#2C3E50'
COLOR_TEXT_SUB = '#7F8C8D'
COLOR_ACCENT = '#1565C0'
COLOR_GREEN = '#27AE60'
COLOR_RED = '#C0392B'
COLOR_REMAINING = '#BDC3C7'

def smart_date_parse(date_str):
    formats = ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%y']
    for fmt in formats:
        try: return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError: pass
    return datetime.now().strftime('%Y-%m-%d')

class MainFrame(wx.Frame):
    def __init__(self, user_id):
        super().__init__(None, title="Financify", size=(1200, 850)) 
        self.user_id = user_id
        self.SetMinSize((1000, 700))
        self.SetBackgroundColour(COLOR_BG)
        self.Center()
        self.Maximize()
        self.InitUI()

    def InitUI(self):
        main_panel = wx.Panel(self)
        main_panel.SetBackgroundColour(COLOR_BG)
        
        self.notebook = wx.Notebook(main_panel)
        self.notebook.SetBackgroundColour(COLOR_BG)
        
        self.dashboard_panel = DashboardPanel(self.notebook, self.user_id)
        self.notebook.AddPage(self.dashboard_panel, "Dashboard")

        self.reports_panel = ReportsPanel(self.notebook, self.user_id)
        self.notebook.AddPage(self.reports_panel, "Reports")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 15)
        main_panel.SetSizer(sizer)
        
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

        # HEADER - Shows Welcome Back Message
        header_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Fetch username for the header
        try:
            uname = db.get_username(self.user_id)
        except:
            uname = "User"
            
        # Reduced font size from 32 to 24 to prevent cut-off
        title = wx.StaticText(self, label=f"Welcome {uname}")
        title.SetFont(wx.Font(24, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title.SetForegroundColour(COLOR_ACCENT)
        header_sizer.Add(title, 0, wx.ALIGN_LEFT | wx.BOTTOM, 5)
        
        date_str = datetime.now().strftime("%A, %d %B %Y")
        subtitle = wx.StaticText(self, label=f"Financial Overview for {date_str}")
        subtitle.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        subtitle.SetForegroundColour(COLOR_TEXT_SUB)
        header_sizer.Add(subtitle, 0, wx.ALIGN_LEFT | wx.BOTTOM, 20)

        main_sizer.Add(header_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 30)

        # CONTENT
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        left_col_sizer = wx.BoxSizer(wx.VERTICAL)
        self.transaction_form = self.CreateTransactionForm(self)
        left_col_sizer.Add(self.transaction_form, 0, wx.EXPAND | wx.BOTTOM, 20)
        self.category_budget_panel = self.CreateCategoryBudgetsPanel(self)
        left_col_sizer.Add(self.category_budget_panel, 1, wx.EXPAND)
        content_sizer.Add(left_col_sizer, 2, wx.EXPAND | wx.RIGHT, 20)

        right_col_sizer = wx.BoxSizer(wx.VERTICAL)
        self.key_numbers_panel = self.CreateKeyNumbersPanel(self)
        right_col_sizer.Add(self.key_numbers_panel, 0, wx.EXPAND | wx.BOTTOM, 20)
        self.pie_chart_panel = self.CreatePieChartPanel(self)
        right_col_sizer.Add(self.pie_chart_panel, 1, wx.EXPAND)
        content_sizer.Add(right_col_sizer, 3, wx.EXPAND)
        
        main_sizer.Add(content_sizer, 1, wx.EXPAND | wx.ALL, 30)
        self.SetSizer(main_sizer)

    def CreateTransactionForm(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(COLOR_BG)
        header_panel = wx.Panel(panel)
        header_panel.SetBackgroundColour(COLOR_WHITE)
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl = wx.StaticText(header_panel, label=" Add New Transaction")
        lbl.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl.SetForegroundColour(COLOR_TEXT_MAIN)
        h_sizer.Add(lbl, 1, wx.ALL, 12)
        header_panel.SetSizer(h_sizer)
        
        form_sizer = wx.BoxSizer(wx.VERTICAL)
        form_sizer.Add(header_panel, 0, wx.EXPAND | wx.BOTTOM, 15)
        
        grid_sizer = wx.FlexGridSizer(rows=6, cols=2, vgap=12, hgap=10)
        self.date_picker = wx.adv.DatePickerCtrl(panel, style=wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY)
        self.date_picker.SetValue(wx.DateTime.Now())
        self.type_choice = wx.Choice(panel, choices=['Expense', 'Income'])
        self.type_choice.SetSelection(0)
        self.amount_ctrl = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.amount_ctrl.SetHint("0.00")
        
        # --- FIXED: Removed SetHint here ---
        self.category_choice = wx.ComboBox(panel, choices=CATEGORIES, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        
        self.desc_ctrl = wx.TextCtrl(panel, size=(-1, 60), style=wx.TE_MULTILINE) 
        
        def make_label(text): 
            t = wx.StaticText(panel, label=text)
            t.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            t.SetForegroundColour(COLOR_TEXT_MAIN)
            return t

        grid_sizer.AddMany([
            (make_label("Date"), 0, wx.ALIGN_CENTER_VERTICAL), (self.date_picker, 1, wx.EXPAND),
            (make_label("Type"), 0, wx.ALIGN_CENTER_VERTICAL), (self.type_choice, 1, wx.EXPAND),
            (make_label("Amount"), 0, wx.ALIGN_CENTER_VERTICAL), (self.amount_ctrl, 1, wx.EXPAND),
            (make_label("Category"), 0, wx.ALIGN_CENTER_VERTICAL), (self.category_choice, 1, wx.EXPAND),
            (make_label("Description"), 0, wx.ALIGN_TOP), (self.desc_ctrl, 1, wx.EXPAND)
        ])
        grid_sizer.AddGrowableCol(1, 1)
        form_sizer.Add(grid_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        
        self.submit_btn = wx.Button(panel, label="Save Transaction", size=(-1, 45))
        self.submit_btn.SetBackgroundColour(COLOR_GREEN)
        self.submit_btn.SetForegroundColour('white')
        self.submit_btn.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.submit_btn.Bind(wx.EVT_BUTTON, self.OnSubmitTransaction)
        form_sizer.Add(self.submit_btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        panel.SetSizer(form_sizer)
        return panel

    def CreateKeyNumbersPanel(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(COLOR_WHITE)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="Monthly Summary")
        lbl.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl.SetForegroundColour(COLOR_TEXT_MAIN)
        main_sizer.Add(lbl, 0, wx.ALL, 20)
        
        budget_sizer = wx.BoxSizer(wx.HORIZONTAL)
        budget_lbl = wx.StaticText(panel, label="Total Budget: ₹")
        budget_lbl.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        budget_sizer.Add(budget_lbl, 0, wx.ALIGN_CENTER_VERTICAL)
        self.budget_ctrl = wx.TextCtrl(panel, value="0.00", size=(100, -1))
        budget_sizer.Add(self.budget_ctrl, 1, wx.LEFT|wx.RIGHT, 10)
        set_btn = wx.Button(panel, label="Update", size=(80, -1))
        set_btn.Bind(wx.EVT_BUTTON, self.OnSetBudget)
        budget_sizer.Add(set_btn, 0)
        main_sizer.Add(budget_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        
        self.income_text = wx.StaticText(panel, label="Income: ₹0.00")
        self.spent_text = wx.StaticText(panel, label="Spent: ₹0.00")
        self.remaining_text = wx.StaticText(panel, label="Remaining: ₹0.00")
        self.net_text = wx.StaticText(panel, label="Net Savings: ₹0.00")
        for t in [self.income_text, self.spent_text, self.remaining_text, self.net_text]:
            t.SetFont(wx.Font(13, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            main_sizer.Add(t, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        self.income_text.SetForegroundColour(COLOR_GREEN)
        self.spent_text.SetForegroundColour(COLOR_RED)
        panel.SetSizer(main_sizer)
        return panel
        
    def CreateCategoryBudgetsPanel(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(COLOR_WHITE)
        layout = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="Category Budgets")
        lbl.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl.SetForegroundColour(COLOR_TEXT_MAIN)
        layout.Add(lbl, 0, wx.ALL, 15)
        self.category_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_NO_HEADER)
        self.category_list.InsertColumn(0, "Category", width=140)
        self.category_list.InsertColumn(1, "Limit", width=100)
        self.category_list.InsertColumn(2, "Spent", width=100)
        self.category_list.InsertColumn(3, "Left", width=100)
        self.category_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnCategorySelected)
        layout.Add(self.category_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_cat_btn = wx.Button(panel, label="Set Limit")
        self.add_cat_btn.Bind(wx.EVT_BUTTON, self.OnAddEditCategory)
        btn_sizer.Add(self.add_cat_btn, 1, wx.RIGHT, 5)
        self.delete_cat_btn = wx.Button(panel, label="Remove")
        self.delete_cat_btn.Bind(wx.EVT_BUTTON, self.OnDeleteCategory)
        self.delete_cat_btn.Disable()
        btn_sizer.Add(self.delete_cat_btn, 1, wx.LEFT, 5)
        layout.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 15)
        panel.SetSizer(layout)
        return panel

    def CreatePieChartPanel(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(COLOR_WHITE)
        layout = wx.BoxSizer(wx.VERTICAL)
        lbl = wx.StaticText(panel, label="Budget Utilization")
        lbl.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl.SetForegroundColour(COLOR_TEXT_MAIN)
        layout.Add(lbl, 0, wx.ALL, 15)
        self.pie_figure = Figure(figsize=(4, 3)) 
        self.pie_figure.set_facecolor(COLOR_WHITE)
        self.pie_axes = self.pie_figure.add_subplot(111) 
        self.pie_canvas = FigureCanvas(panel, -1, self.pie_figure)
        layout.Add(self.pie_canvas, 1, wx.EXPAND | wx.ALL, 15)
        panel.SetSizer(layout)
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
        self.remaining_text.SetLabel(f"Remaining: ₹{data['remaining']:.2f}")
        self.net_text.SetLabel(f"Net Savings: ₹{data['net']:.2f}")
        
        if data['remaining'] < 0: self.remaining_text.SetForegroundColour(COLOR_RED)
        else: self.remaining_text.SetForegroundColour(COLOR_ACCENT) 
        if data['net'] < 0: self.net_text.SetForegroundColour(COLOR_RED)
        else: self.net_text.SetForegroundColour(COLOR_GREEN)

        self.pie_axes.clear()
        total_budget = data['budget']
        expense_data = db.get_expense_data_for_pie_chart(self.user_id, month, year)
        
        labels, sizes, colors = [], [], []
        std_colors = ['#3498DB', '#E74C3C', '#2ECC71', '#F1C40F', '#9B59B6', '#E67E22', '#1ABC9C', '#34495E']
        
        total_spent = 0
        for i, row in enumerate(expense_data):
            labels.append(row['category'])
            sizes.append(row['total'])
            colors.append(std_colors[i % len(std_colors)])
            total_spent += row['total']
            
        if total_budget > 0:
            remaining = total_budget - total_spent
            if remaining > 0:
                labels.append("Remaining")
                sizes.append(remaining)
                colors.append(COLOR_REMAINING)
            self.pie_axes.set_title(f'Monthly Budget: ₹{total_budget:.0f}')
        else:
            self.pie_axes.set_title(f'Spending Breakdown')

        if not sizes:
            self.pie_axes.text(0.5, 0.5, 'No Data', ha='center', va='center')
        else:
            def my_autopct(pct): return '%1.1f%%' % pct if pct > 5 else '' 
            wedges, texts, autotexts = self.pie_axes.pie(sizes, labels=None, autopct=my_autopct, startangle=90, colors=colors)
            self.pie_axes.legend(wedges, labels, title="Categories", loc="center left", bbox_to_anchor=(0.9, 0, 0.5, 1))

        self.pie_figure.tight_layout()
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
            else: self.category_list.SetItemTextColour(index, COLOR_ACCENT)
        self.selected_category = None
        self.delete_cat_btn.Disable()

    def OnSubmitTransaction(self, event):
        try:
            date_obj = self.date_picker.GetValue()
            date_str = date_obj.FormatISODate()
            trans_type = self.type_choice.GetStringSelection()
            amount_str = self.amount_ctrl.GetValue()
            category = self.category_choice.GetValue()
            description = self.desc_ctrl.GetValue()

            if not amount_str: raise ValueError("Please enter an amount.")
            try: amount = float(amount_str)
            except ValueError: raise ValueError("Amount must be a number.")
            if amount <= 0: raise ValueError("Amount must be greater than 0.")
            if not category: raise ValueError("Please select a category.")

            if trans_type == 'Expense':
                cat_budgets = db.get_category_budgets_with_spending(self.user_id, datetime.now().month, datetime.now().year)
                this_cat = next((item for item in cat_budgets if item['category'] == category), None)
                if this_cat and this_cat['budget'] > 0:
                    if (this_cat['spent'] + float(amount)) > this_cat['budget']:
                         wx.MessageBox(f"⚠️ Alert: This transaction exceeds your {category} budget!", "Budget Warning", wx.OK|wx.ICON_WARNING)

            success, message, _ = db.add_transaction(self.user_id, self.default_account_id, date_str, amount, trans_type, category, description, tags="")
            if not success: raise Exception(message)
            
            wx.MessageBox("Transaction added successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
            self.ClearForm()
            wx.GetApp().GetTopWindow().RefreshAllTabs()
        except Exception as e: wx.MessageBox(f"Error: {str(e)}", "Input Error", wx.OK | wx.ICON_ERROR)

    def ClearForm(self):
        self.date_picker.SetValue(wx.DateTime.Now())
        self.type_choice.SetSelection(0)
        self.amount_ctrl.SetValue("")
        self.category_choice.SetSelection(wx.NOT_FOUND)
        self.desc_ctrl.SetValue("")

    def OnSetBudget(self, event):
        try:
            val = self.budget_ctrl.GetValue()
            if not val: return
            amount = float(val)
            if amount < 0: raise ValueError
            db.set_monthly_budget(self.user_id, datetime.now().month, datetime.now().year, amount)
            self.RefreshData()
        except ValueError: wx.MessageBox("Please enter a valid number for the budget.", "Error")

    def OnCategorySelected(self, event):
        self.selected_category = self.category_list.GetItemText(event.GetIndex(), 0)
        self.delete_cat_btn.Enable()
    
    def OnAddEditCategory(self, event):
        today = datetime.now()
        all_cats = set(CATEGORIES)
        current_budgets = db.get_category_budgets_with_spending(self.user_id, today.month, today.year)
        used_cats = {item['category'] for item in current_budgets}
        available_cats = [c for c in all_cats if c not in used_cats and c != 'Salary']
        available_cats.sort()
        
        if not available_cats:
            wx.MessageBox("All categories already have budgets set!", "Info")
            return

        dlg = CategoryBudgetDialog(self, available_cats)
        if dlg.ShowModal() == wx.ID_OK:
            cat, amt = dlg.GetValues()
            if cat and amt > 0:
                db.set_category_budget(self.user_id, cat, amt, today.month, today.year)
                self.RefreshData()
        dlg.Destroy()
    
    def OnDeleteCategory(self, event):
        if not self.selected_category: return
        if wx.MessageBox(f"Remove budget limit for '{self.selected_category}'?", "Confirm Delete", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            db.delete_category_budget(self.user_id, self.selected_category, datetime.now().month, datetime.now().year)
            wx.MessageBox(f"Budget limit for '{self.selected_category}' has been removed.\nNote: If you have existing expenses, the category will remain in the list.", "Success")
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
        main_sizer.Add(self.bar_chart_panel, 1, wx.EXPAND | wx.ALL, 15)

        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.search_ctrl = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.search_ctrl.SetDescriptiveText("Search transactions...")
        self.search_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.search_ctrl.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        toolbar_sizer.Add(self.search_ctrl, 1, wx.EXPAND | wx.RIGHT, 10)
        self.import_btn = wx.Button(self, label="Import CSV")
        self.import_btn.Bind(wx.EVT_BUTTON, self.OnImportCSV)
        toolbar_sizer.Add(self.import_btn, 0, wx.RIGHT, 5)
        self.export_btn = wx.Button(self, label="Export CSV")
        self.export_btn.Bind(wx.EVT_BUTTON, self.OnExportCSV)
        toolbar_sizer.Add(self.export_btn, 0, wx.RIGHT, 5)
        self.report_btn = wx.Button(self, label="HTML Report")
        self.report_btn.Bind(wx.EVT_BUTTON, self.OnGenerateReport)
        toolbar_sizer.Add(self.report_btn, 0, wx.RIGHT, 5)
        self.reset_btn = wx.Button(self, label="Reset All Data")
        self.reset_btn.SetForegroundColour(COLOR_RED)
        self.reset_btn.Bind(wx.EVT_BUTTON, self.OnReset)
        toolbar_sizer.Add(self.reset_btn, 0)
        main_sizer.Add(toolbar_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.trans_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES)
        self.trans_list.InsertColumn(0, "ID", width=0)
        self.trans_list.InsertColumn(1, "Date", width=120)
        self.trans_list.InsertColumn(2, "Type", width=100)
        self.trans_list.InsertColumn(3, "Amount", width=120, format=wx.LIST_FORMAT_RIGHT)
        self.trans_list.InsertColumn(4, "Category", width=150)
        self.trans_list.InsertColumn(5, "Account", width=0)
        self.trans_list.InsertColumn(6, "Description", width=300)
        main_sizer.Add(self.trans_list, 2, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        self.SetSizer(main_sizer)
        self.trans_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickTransaction)
        self.selected_trans_id = None

    def CreateBarChartPanel(self, parent):
        panel = wx.Panel(parent, style=wx.BORDER_SIMPLE)
        panel.SetBackgroundColour(COLOR_WHITE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.bar_figure = Figure(figsize=(5, 2.5)) 
        self.bar_figure.set_facecolor(COLOR_WHITE)
        self.bar_axes = self.bar_figure.add_subplot(111) 
        self.bar_canvas = FigureCanvas(panel, -1, self.bar_figure)
        sizer.Add(self.bar_canvas, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        return panel

    def RefreshData(self, search_term=""):
        bar_data = db.get_monthly_comparison_data(self.user_id)
        self.bar_axes.clear()
        if not bar_data: 
            self.bar_axes.text(0.5, 0.5, 'No Data Available', ha='center')
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
            self.bar_axes.set_title('Income vs Expenses Trend')
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
        wx.MessageBox("Transaction cloned successfully!", "Success")

    def OnEdit(self, event):
        trans = [t for t in db.get_transactions_by_filter(self.user_id) if t['transaction_id'] == self.selected_trans_id]
        if not trans: return
        dlg = TransactionEditDialog(self, self.user_id, trans[0], db.get_accounts(self.user_id))
        if dlg.ShowModal() == wx.ID_OK: wx.GetApp().GetTopWindow().RefreshAllTabs()
        dlg.Destroy()

    def OnDelete(self, event):
        if wx.MessageBox("Are you sure you want to delete this transaction?", "Confirm Delete", wx.YES_NO | wx.ICON_WARNING) == wx.YES:
            db.delete_transaction(self.selected_trans_id, self.user_id)
            wx.GetApp().GetTopWindow().RefreshAllTabs()

    def OnGenerateReport(self, event):
        path = os.path.abspath("report.html")
        rows = db.get_transactions_by_filter(self.user_id)
        html = "<html><body style='font-family: sans-serif; padding: 20px;'>"
        html += "<h1 style='color: #2C3E50;'>Financify Transaction Report</h1>"
        html += f"<p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>"
        html += "<table border='1' cellspacing='0' cellpadding='8' style='width:100%; border-collapse: collapse;'>"
        html += "<tr style='background-color: #ECF0F1;'><th>Date</th><th>Type</th><th>Amount</th><th>Category</th><th>Description</th></tr>"
        for r in rows:
            color = "green" if r['type']=='Income' else "red"
            html += f"<tr><td>{r['date']}</td><td>{r['type']}</td><td style='color:{color}; font-weight:bold;'>{r['amount']}</td><td>{r['category']}</td><td>{r['description']}</td></tr>"
        html += "</table></body></html>"
        with open(path, "w") as f: f.write(html)
        webbrowser.open('file://' + path)

    def OnExportCSV(self, event):
        with wx.FileDialog(self, "Save CSV", wildcard="*.csv", style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() == wx.ID_CANCEL: return
            try:
                rows = db.get_transactions_by_filter(self.user_id)
                with open(dlg.GetPath(), 'w', newline='', encoding='utf-8') as f:
                    w = csv.DictWriter(f, fieldnames=rows[0].keys())
                    w.writeheader()
                    for r in rows: w.writerow(dict(r))
                wx.MessageBox("Data exported successfully!", "Export")
            except Exception as e: wx.MessageBox(str(e))

    def OnImportCSV(self, event):
        with wx.FileDialog(self, "Open CSV", wildcard="*.csv", style=wx.FD_OPEN) as dlg:
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
                wx.MessageBox("CSV Imported successfully!", "Import")
                wx.GetApp().GetTopWindow().RefreshAllTabs()
            except Exception as e: wx.MessageBox(str(e))

    def OnReset(self, event):
        if wx.MessageBox("⚠️ WARNING: This will permanently delete ALL your data.\nAre you sure?", "FACTORY RESET", wx.YES_NO|wx.ICON_ERROR) == wx.YES:
            db.wipe_user_data(self.user_id)
            wx.GetApp().GetTopWindow().RefreshAllTabs()
            wx.MessageBox("All data has been wiped.", "Reset Complete")

class CategoryBudgetDialog(wx.Dialog):
    def __init__(self, parent, available_categories):
        # We DO NOT set a fixed height here anymore to avoid clipping. 
        # We rely on wxPython to calculate the best size.
        super().__init__(parent, title="Set Category Budget")
        self.Center()
        panel = wx.Panel(self)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        v_sizer.Add(wx.StaticText(panel, label="Select Category"), 0, wx.ALL, 10)
        self.cat_choice = wx.Choice(panel, choices=available_categories)
        self.cat_choice.SetSelection(0)
        v_sizer.Add(self.cat_choice, 0, wx.EXPAND|wx.ALL, 10)
        v_sizer.Add(wx.StaticText(panel, label="Budget Amount (₹)"), 0, wx.ALL, 10)
        self.amt_ctrl = wx.TextCtrl(panel)
        v_sizer.Add(self.amt_ctrl, 0, wx.EXPAND|wx.ALL, 10)
        btn_sizer = wx.StdDialogButtonSizer()
        btn_sizer.AddButton(wx.Button(panel, wx.ID_OK))
        btn_sizer.AddButton(wx.Button(panel, wx.ID_CANCEL))
        btn_sizer.Realize()
        v_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 20)
        panel.SetSizer(v_sizer)
        
        # --- KEY FIX: Auto-Fit + Add padding to ensure nothing is clipped ---
        v_sizer.Fit(panel)
        self.SetClientSize(panel.GetSize())
        self.SetMinSize(self.GetSize())

    def GetValues(self):
        try: amt = float(self.amt_ctrl.GetValue())
        except ValueError: amt = 0.0
        return self.cat_choice.GetStringSelection(), amt

class TransactionEditDialog(wx.Dialog):
    def __init__(self, parent, user_id, t, accounts):
        # Using auto-fit logic instead of hardcoding height
        super().__init__(parent, title="Edit Transaction")
        self.user_id, self.t, self.accs, self.amap = user_id, t, accounts, {}
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.date = wx.adv.DatePickerCtrl(panel)
        self.type = wx.Choice(panel, choices=['Expense', 'Income'])
        self.amt = wx.TextCtrl(panel)
        self.cat = wx.ComboBox(panel, choices=CATEGORIES)
        self.desc = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 60))
        for label, ctrl in [("Date", self.date), ("Type", self.type), ("Amount", self.amt), ("Category", self.cat), ("Description", self.desc)]:
            sizer.Add(wx.StaticText(panel, label=label), 0, wx.TOP|wx.LEFT, 10)
            sizer.Add(ctrl, 0, wx.EXPAND|wx.ALL, 10)
        self.LoadData()
        btn_sizer = wx.StdDialogButtonSizer()
        save_btn = wx.Button(panel, wx.ID_OK, "Save Changes")
        btn_sizer.AddButton(save_btn)
        btn_sizer.AddButton(wx.Button(panel, wx.ID_CANCEL))
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 15)
        panel.SetSizer(sizer)
        save_btn.Bind(wx.EVT_BUTTON, self.OnSave)
        
        # --- KEY FIX: Auto-Fit ---
        sizer.Fit(panel)
        self.SetClientSize(panel.GetSize())
        self.SetMinSize(self.GetSize())

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
        except: wx.MessageBox("Invalid Input", "Error", wx.ICON_ERROR)
