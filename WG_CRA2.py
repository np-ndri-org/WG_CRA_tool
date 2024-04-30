# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 14:08:55 2019

Dibesh Shrestha, dibeshshrestha@live.com
Divas B.Basnyat,Ph.D, divas@ndri.org.np
Nepal Development Research Institue
August, 2019
"""
import os
from datetime import datetime
import time
import calendar
import sys
import pandas as pd
import numpy as np
import wx
import wx.adv
import wx.lib.intctrl
import wx.lib.masked.numctrl
import wx.grid as gridlib
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import statsmodels.api as sm
import statsmodels
from statsmodels.tsa.arima_process import ArmaProcess
from scipy import stats
# Importing weather generator
import wg
import xarray as xr
import xesmf as xe
import cdo as CDO
import xrft
from statsmodels.distributions.empirical_distribution import ECDF
#%%
mpl.rcParams.update({'font.size': 4})
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

Logo = resource_path('WGicon.png')
LogoNDRI = resource_path('NDRI.png')
LogoAPN = resource_path('APNicon_sample.png')
#%%
class RedirectText(object):
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl

    def write(self,string ):
        wx.CallAfter(self.out.WriteText, string)
#%%
class WGFrame(wx.Frame):
    """ We are defining frame for Weather Generator """
    def __init__(self,parent,title):
        wx.Frame.__init__(self,parent,title=title,size = (900,800)) #size = (900,600)

        self.CreateStatusBar() # Status bar in the bottom of the window

        #Setting up the menu
        filemenu = wx.Menu()
        # Providing the ids to different items in Menubar
        # Using the inbulit IDs that are made by wx
        menuAbout = filemenu.Append(wx.ID_ABOUT,"&About","Information about this program")
        menuExit = filemenu.Append(wx.ID_EXIT,"E&xit","Exit the program")

        #Creating the menubar
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"General") #Adding the file menu to the Menubar
        self.SetMenuBar(menuBar) #Adding the MenuBar to the Frame content

        #Setting events
        self.Bind(wx.EVT_MENU,self.OnAbout,menuAbout)
        self.Bind(wx.EVT_MENU,self.OnExit,menuExit)
        self.Bind(wx.EVT_CLOSE,self.closewindow)

            #Creating the notebook (different pages: three pages)
        #nb = aui.AuiNotebook(frame) wx.Notebook(frame)
        self.p = wx.Panel(self,style = wx.RAISED_BORDER)
        self.nb = wx.Notebook(self.p)
        self.nb.AddPage(ABOUT(self.nb),"")
        self.nb.AddPage(AnnualSeriesSimulator(self.nb), "Annual Series Simulator")
        self.nb.AddPage(WGCRA(self.nb),"WG-CRA")
        self.nb.AddPage(KnnWG(self.nb), "k-NN WG")
        self.nb.AddPage(CCSG(self.nb), "CC Scenario Generator")
        self.nb.AddPage(BCSD(self.nb), "BCSD")
        self.nb.AddPage(ResultViewerPanel(self.nb), "Result viewer")
        self.nb.AddPage(DESCRIPTION(self.nb),"Brief Description")

        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.p.SetSizer(sizer)
        sizer.Fit(self.p)
        self.p.Layout()

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED,self.OnPageChanged,self.nb)

    def OnPageChanged(self,event):
        x = self.nb.GetSelection()
        y = self.nb.GetPageText(x)
        self.SetStatusText("Current page: {}".format(y))
#        if y == "k-NN WG":
#            sys.stdout = self.nb.KnnWG.logger1
#        if y == "CC Senario Generator":
#            sys.stdout = self.nb.CCSG.logger

    def OnAbout(self,event):
        """ Display the information about the program in message box. """
        # Message box with an OK button
        textmsg = """Weather Generator and Climate Change Scenario Generator for Climate Risk Assessment (version 0.1.0 BETA)\n
        \nThis tool aims to support Climate Risk Assessment.\nDeveloped by: \nDibesh Shrestha\nDivas B. Basnyat, Ph.D\nNepal Development Research Institute\nNepal\nAugust 2019
        """
        dlg = wx.MessageDialog(self,textmsg,"About this program!",wx.OK)
        dlg.ShowModal() #Show the messagebox
        dlg.Destroy() #Destroy the messagebox when finished

    def OnExit(self,event):
        self.Close(True) #Close the frame

    def closewindow(self,event):
        self.Destroy()

#%%
class VarSelectionFrame(wx.Dialog):
    """Frame for the variable selection"""
    def __init__(self,parent,title,var_list):
        self.var_list = var_list.copy();
        self.original_var_list = var_list.copy()
        self.selectedVarList = []

        wx.Dialog.__init__(self,parent,title=title,size = (400,400))
        panel = wx.Panel(self) # Create panel

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        grid = wx.FlexGridSizer(3,2,5,5)
        #Create an static text box calles text0
        self.text0 = wx.StaticText(panel,label = "Data Columns")
        # Add to the sizer grid
        grid.Add(self.text0, border = 10)

        #Create an static text box calles text0
        self.text1 = wx.StaticText(panel,label = "Selected Variable Columns")
        # Add to the sizer grid
        grid.Add(self.text1, border = 10)

        self.text3 = wx.TextCtrl(panel,style = wx.TE_MULTILINE)
        self.lst = wx.ListBox(panel, size = (100,-1), choices = self.var_list, style = wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX, self.onListBox, self.lst)

        grid.Add(self.lst,flag = wx.ALL|wx.EXPAND, border = 5)
        grid.Add(self.text3, flag= wx.ALL|wx.EXPAND, border = 5)

        self.clearButton = wx.Button(panel,id = wx.ID_ANY,label = 'Clear')
        grid.Add(self.clearButton, flag= wx.EXPAND, border = 10)
        self.clearButton.Bind(wx.EVT_BUTTON,self.clearContents)

        self.okButton = wx.Button(panel,id = wx.ID_ANY,label = 'Ok')
        grid.Add(self.okButton, flag= wx.EXPAND, border = 10)
        self.okButton.Bind(wx.EVT_BUTTON,self.readVars)

        grid.AddGrowableRow(1, 1)
        grid.AddGrowableCol(1, 2)

        hbox.Add(grid, proportion = 2, flag = wx.ALL|wx.EXPAND, border = 5)
        panel.SetSizerAndFit(hbox)
        self.Centre()
        self.Show()

    def onListBox(self, event):
        selected_item = event.GetEventObject().GetStringSelection()
        self.text3.AppendText(selected_item +"\n")
        self.var_list.remove(selected_item)
        self.lst.Set(self.var_list)

    def clearContents(self,event):
        self.text3.SetLabel('')
        self.var_list = self.original_var_list.copy()
        self.lst.Set(self.original_var_list)

    def readVars(self,event):
        n = self.text3.GetNumberOfLines()
        if n == 1:
            textmsg = """None variables selected. Select variables!"""
            dlg1 = wx.MessageDialog(self,textmsg,"Select variables ",wx.OK)
            dlg1.ShowModal() #Show the messagebox
            dlg1.Destroy() #Destroy the messagebox when finished)
        else:
            for i in range(n-1):
                self.selectedVarList.append(self.text3.GetLineText(i))
            self.Close()

    def update_selectedVarList(self,var_to_update):
        self.selectedVarList = var_to_update.copy()

    def get_selectedVarList(self):
        return self.selectedVarList
#%%
class SetPathVariableFilesFrame(wx.Dialog):
    """Frame for setting path to varaible files"""
    def __init__(self,parent,title,sel_var_list,style = wx.OK | wx.CANCEL):
        self.sel_var_list = sel_var_list;
        self.sel_var_path = dict();
        self.Buttons = dict()
        self.StaticBoxs = dict()
        self.varnames = dict()
        self.flag = 0

        wx.Dialog.__init__(self,parent,title=title)
        panel1 = wx.Panel(self) # Create panel

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        grid = wx.FlexGridSizer(len(self.sel_var_list),2,5,5)

        # Put load the data box
        #Create an button to load main data
        for row, varname in enumerate(self.sel_var_list):
            nm = "Load " + varname
            B = wx.Button(panel1, label = nm)
            S = wx.TextCtrl(panel1,value = "", size =(200,-1),style =wx.TE_MULTILINE|wx.TE_READONLY, name = str(B.GetId()))
            grid.Add(B, flag = wx.ALL, border = 5)
            grid.Add(S, flag = wx.ALL|wx.EXPAND, border = 5)
            B.Bind(wx.EVT_BUTTON,self.LoadVarData)
            self.Buttons[B.GetId()] = B
            self.varnames[B.GetId()] = varname
            self.StaticBoxs[str(B.GetId())] = S

        closeButton = wx.Button(panel1,label = "Set path,load and Close")
        closeButton.Bind(wx.EVT_BUTTON,self.OnCloseButton)
        cancelClose = wx.Button(panel1,label = "Cancel and Close")
        cancelClose.Bind(wx.EVT_BUTTON,self.closewindow)

        self.Bind(wx.EVT_CLOSE,self.closewindow)

        for i in range(len(self.sel_var_list)):
            grid.AddGrowableRow(i,1)

        hbox.Add(grid, proportion = 1, flag = wx.ALL|wx.EXPAND, border = 0)
        vbox.Add(hbox,proportion = 1, flag = wx.ALL|wx.EXPAND, border = 0)
        vbox.Add(closeButton, proportion = 0,flag = wx.ALL|wx.EXPAND, border = 5)
        vbox.Add(cancelClose,proportion = 0,flag = wx.ALL|wx.EXPAND, border = 5)

        panel1.SetSizerAndFit(vbox)
        self.Fit()
        self.Centre()
        self.Show()

    def LoadVarData(self,event):
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose Data file", self.dirname, "", "*.*", wx.FD_OPEN)
        self.store = {}
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            key = self.varnames[event.GetEventObject().GetId()]
            self.sel_var_path[key] = f;
            self.store[key] = f
            self.StaticBoxs[str(event.GetEventObject().GetId())].SetLabel(f)

    def check(self):
        for k in self.sel_var_list:
            if k not in self.sel_var_path.keys():
                return (0,k)
        return 1

    def OnCloseButton(self,event):
        ch_result = self.check()
        def OnCloseButton2(self):
            self.Destroy()
        if ch_result == 1:
            self.flag = 1
            self.Bind(wx.EVT_CLOSE,OnCloseButton2(self))
            OnCloseButton2(self)
        else:
            textmsg = "Please choose file for " + ch_result[1]+ " variable!"
            dlg = wx.MessageDialog(self,textmsg,"Reminder! ",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)

    def closewindow(self,event):
        self.sel_var_path = dict();
        self.Destroy()
#%%
class WeightsFrame(wx.Dialog):
    """Frame for giving weights to the variables"""
    def __init__(self,parent,title,sel_var_list,precip_var_name,nature):
        # nature is 'weights' and 'values'
        self.sel_var_list = sel_var_list;
        self.sel_var_weights = [];
        self.TC = dict()
        self.precip_name = precip_var_name
        self.nature = nature
        wx.Dialog.__init__(self,parent,title=title)
        panel1 = wx.Panel(self) # Create panel

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        grid = wx.FlexGridSizer(len(self.sel_var_list),2,5,5)

        # Put load the data box
        #Create an button to load main data
        for row, varname in enumerate(self.sel_var_list):
            B = wx.StaticText(panel1, label = varname)
            if self.nature == 'weights':
                T = wx.lib.masked.numctrl.NumCtrl(panel1,value = 1.0, \
                                   style = wx.TE_PROCESS_ENTER, \
                                   integerWidth = 5, fractionWidth=2, \
                                   min = 0, max = 100, limited = 1,\
                                   allowNegative=False, allowNone = True,
                                   name = str(B.GetId()))
            else:
                 if self.precip_name == varname:
                     T = wx.lib.masked.numctrl.NumCtrl(panel1,value = 1.0, \
                                   style = wx.TE_PROCESS_ENTER, \
                                   integerWidth = 7, fractionWidth=2, \
                                   min = 0, max = 100, limited = 1,\
                                   allowNegative=False, allowNone = True,
                                   name = str(B.GetId()))
                 else:
                      T = wx.lib.masked.numctrl.NumCtrl(panel1,value = 1.0, \
                                   style = wx.TE_PROCESS_ENTER, \
                                   integerWidth = 8, fractionWidth=2, \
                                   min = -200, max = 200, limited = 1,\
                                   allowNegative=True, allowNone = True,
                                   name = str(B.GetId()))
            grid.Add(B, flag = wx.ALL|wx.EXPAND, border = 5)
            grid.Add(T, flag = wx.ALL|wx.EXPAND, border = 5)
            self.TC[varname] = T

        OkButton = wx.Button(panel1,label = "Ok")
        OkButton.Bind(wx.EVT_BUTTON,self.OnOk)

        # Binding the close button of the window
        self.Bind(wx.EVT_CLOSE,self.OnDestroy)

        for i in range(len(self.sel_var_list)):
            grid.AddGrowableRow(i,1)

        hbox.Add(grid, proportion = 0, flag = wx.ALL|wx.EXPAND, border = 0)
        vbox.Add(hbox,proportion = 0, flag = wx.ALL|wx.EXPAND, border = 0)
        vbox.Add(OkButton, proportion = 0,flag = wx.ALL|wx.EXPAND, border = 5)

        panel1.SetSizerAndFit(vbox)
        self.Fit()
        self.Centre()
        self.Show()

    def OnOk(self,event):
        for row, varname in enumerate(self.sel_var_list):
            self.sel_var_weights.append(float(self.TC[varname].GetLineText(0)))
        self.Close()

    def OnDestroy(self,event):
        if len(self.sel_var_weights) == 0:
            for row, varname in enumerate(self.sel_var_list):
                self.sel_var_weights.append(float(self.TC[varname].GetLineText(0)))
        self.Destroy()
#%% TP frame
class TP_Frame_View(wx.Dialog):
    """Frame for giving weights to the variables"""
    def __init__(self,parent,title,TP,nstates):
        self.TP = TP
        self.originalTP = TP
        self.nstates = nstates

        wx.Dialog.__init__(self,parent,title=title)

        if self.nstates == 2:
            ncols = 4
            collabels = ['p00','p01','p10','p11']
        elif self.nstates == 3:
            ncols = 9
            collabels = ['p00','p01','p02','p10','p11','p12','p20','p21','p22']

        self.collabels = collabels
        self.pdindex = [calendar.month_abbr[i+1] for i in range(12)]

        self.panel1 = wx.Panel(self) # Create panel

        self.vbox = wx.BoxSizer(wx.VERTICAL)

        # Create an static text box named text for declaring precipitation column
        self.text0 = wx.StaticText(self.panel1, label = "Original Transition Probability")
        self.vbox.Add(self.text0, flag = wx.ALL, border = 5)

        # View
        self.viewGrid = gridlib.Grid(self.panel1)
        # creating grid for viewing
        self.viewGrid.CreateGrid(12,ncols)
        for j in range(0,ncols):
            self.viewGrid.SetColLabelValue(j,collabels[j])
        for i in range(12):
            self.viewGrid.SetRowLabelValue(i,calendar.month_abbr[i+1])
        TPvalues = self.TP.values
        ncols1 = self.viewGrid.GetNumberCols()
        nrows1 = self.viewGrid.GetNumberRows()
        for rows in range(nrows1):
            for cols in range(ncols1):
                self.viewGrid.SetCellEditor(rows, cols, \
                                              gridlib.GridCellFloatEditor(width = 10, precision = 6))
                self.viewGrid.SetCellValue(rows,cols,str(np.round(TPvalues[rows,cols],3)))
                self.viewGrid.SetReadOnly(rows, cols, True)
        self.viewGrid.Enable()
        self.vbox.Add(self.viewGrid,flag = wx.ALL|wx.EXPAND, border = 5)

        # save
        self.SaveOriginalTP = wx.Button(self.panel1, label = "Save")
        self.vbox.Add(self.SaveOriginalTP, flag = wx.ALL, border = 5)
        self.SaveOriginalTP.Bind(wx.EVT_BUTTON, self.OnSaveOriginalTP)

        # Binding the close button of the window
        self.Bind(wx.EVT_CLOSE,self.OnDestroy)

        self.panel1.SetSizerAndFit(self.vbox)
        self.Fit()
        self.Centre()
        self.Show()

    def OnSaveOriginalTP(self,event):
        with wx.FileDialog(self, "Save TP file", wildcard="CSV files (*.csv)|*.csv",
                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                TP = self.originalTP.round(3)
                TP.to_csv(pathname)
                #with open(pathname, 'w') as file:
                    #self.doSaveData(file)
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)

    def OnDestroy(self,event):
        self.Destroy()
#%%
class TP_Frame_Change(wx.Dialog):
    """Frame for giving weights to the variables"""
    def __init__(self,parent,title,TP=None,nstates=3):
        self.TP = TP
        self.originalTP = TP
        self.nstates = nstates

        wx.Dialog.__init__(self,parent,title=title)

        if self.nstates == 2:
            ncols = 4
            collabels = ['p00','p01','p10','p11']
        elif self.nstates == 3:
            ncols = 9
            collabels = ['p00','p01','p02','p10','p11','p12','p20','p21','p22']
        self.collabels = collabels
        self.pdindex = [i+1 for i in range(12)]

        datavalues = np.zeros((12,ncols))
        self.newTPch = pd.DataFrame(data = datavalues, index = self.pdindex, columns = self.collabels)

        self.panel = wx.Panel(self)
        self.box = wx.BoxSizer(wx.VERTICAL)

        self.text0 = wx.StaticText(self.panel, label = "Original Transition Probability")
        self.box.Add(self.text0,flag = wx.ALL, border = 5)

        self.viewGrid = gridlib.Grid(self.panel)
        self.viewGrid.CreateGrid(12,ncols)
        for j in range(0,ncols):
            self.viewGrid.SetColLabelValue(j,collabels[j])
        for i in range(12):
            self.viewGrid.SetRowLabelValue(i,calendar.month_abbr[i+1])
        TPvalues = self.TP
        ncols0 = self.viewGrid.GetNumberCols()
        nrows0 = self.viewGrid.GetNumberRows()
        for rows in range(nrows0):
            for cols in range(ncols0):
                self.viewGrid.SetCellEditor(rows, cols, \
                                              gridlib.GridCellFloatEditor(width = 10, precision = 3))
                self.viewGrid.SetCellValue(rows,cols,str(np.round(TPvalues.iloc[rows,cols],3)))
                self.viewGrid.SetReadOnly(rows, cols, True)
        self.viewGrid.Enable()
        self.box.Add(self.viewGrid,flag = wx.ALL|wx.EXPAND, border = 5)

        self.box1 = wx.BoxSizer(wx.HORIZONTAL)

        self.B = wx.Button(self.panel,label = "Load TP Change file")
        self.box1.Add(self.B,1, wx.ALL, 5)
        self.B.Bind(wx.EVT_BUTTON,self.onB)

        lbl = """Note: Sum of changes in probabilities for given predecessor state should be zero.
                       And value of changes in individual probabilities should be between -1 and +1. """
        self.text1 = wx.StaticText(self.panel, label = lbl)
        self.box1.Add(self.text1,flag = wx.ALL, border = 5)

        self.box.Add(self.box1,flag = wx.ALL, border = 5)

        self.chGrid = gridlib.Grid(self.panel)
        self.chGrid.CreateGrid(12,ncols)
        for j in range(0,ncols):
            self.chGrid.SetColLabelValue(j,collabels[j])
        for i in range(12):
            self.chGrid.SetRowLabelValue(i,calendar.month_abbr[i+1])
        ncols1 = self.chGrid.GetNumberCols()
        nrows1 = self.chGrid.GetNumberRows()
        for rows in range(nrows1):
            for cols in range(ncols1):
                self.chGrid.SetCellEditor(rows, cols, \
                                              gridlib.GridCellFloatEditor(width = 5, precision = 2))
                self.chGrid.SetCellValue(rows,cols,'0.00')
        self.chGrid.Enable()
        self.box.Add(self.chGrid,flag = wx.ALL|wx.EXPAND, border = 5)

        self.box2 = wx.BoxSizer(wx.HORIZONTAL)

        self.LoadFromBox = wx.Button(self.panel,label = "Load from box")
        self.box2.Add(self.LoadFromBox,1,wx.ALL,5)
        self.LoadFromBox.Bind(wx.EVT_BUTTON,self.OnLoadFromBox)

        self.CloseButton = wx.Button(self.panel,id = wx.ID_CLOSE, label = "Close")
        self.box2.Add(self.CloseButton,1,wx.ALL,5)
        self.CloseButton.Bind(wx.EVT_BUTTON,self.OnClose)

        self.box.Add(self.box2,flag = wx.ALL, border = 5)

        self.panel.SetSizerAndFit(self.box)
        self.Fit()
        self.Centre()
        self.Show()

    def onB(self,event):
        with wx.FileDialog(self, "Open TP Change file", wildcard="CSV files (*.csv)|*.csv", \
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            pathname = fileDialog.GetPath()
            try:
                newTPch = pd.read_csv(pathname,header = 0,index_col='month',parse_dates=True)
                CheckStatus = self.CheckTPsum(newTPch) & self.CheckTPindividual(newTPch)
                if CheckStatus is True:
                    self.newTPch = newTPch
                else:
                    msg = """Sum of changes in probabilities doesn't add upto 0. \n
                            Or Sum of individual changes is not between -1 and +1. \n
                            Data is loaded below. Please correct and press 'Load from Box'"""
                    dlg1 = wx.MessageDialog(self,msg,"Error Message",wx.OK)
                    dlg1.ShowModal() #Show the messagebox
                    dlg1.Destroy() #Destroy the messagebox when finished)
            except Exception as e:
                dlg = wx.MessageDialog(self,str(e),"Error Message",wx.OK)
                dlg.ShowModal() #Show the messagebox
                dlg.Destroy() #Destroy the messagebox when finished)

        try:
            TPchvalues = newTPch
            ncols2 = self.chGrid.GetNumberCols()
            nrows2 = self.chGrid.GetNumberRows()
            for rows in range(nrows2):
                for cols in range(ncols2):
                    # np.round(TPvalues[rows,cols],3)
                    self.chGrid.SetCellValue(rows,cols,str(np.round(TPchvalues.iloc[rows,cols],2)))
        except Exception as e:
            ncols2 = self.chGrid.GetNumberCols()
            nrows2 = self.chGrid.GetNumberRows()
            for rows in range(nrows2):
                for cols in range(ncols2):
                    self.chGrid.SetCellValue(rows,cols,'0.00')
            dlg1 = wx.MessageDialog(self,str(e),"Error Message",wx.OK)
            dlg1.ShowModal() #Show the messagebox
            dlg1.Destroy() #Destroy the messagebox when finished)

    def OnLoadFromBox(self,event):
        try:
            ncols2 = self.chGrid.GetNumberCols()
            nrows2 = self.chGrid.GetNumberRows()
            listvalues = []
            for rows in range(nrows2):
                listrow = []
                for cols in range(ncols2):
                    cellvalue = float(self.chGrid.GetCellValue(rows,cols))
                    listrow.append(cellvalue)
                listvalues.append(listrow)
            datavalues = np.array(listvalues)
            newTPch = pd.DataFrame(data = datavalues, index = self.pdindex, columns = self.collabels)
            CheckStatus = self.CheckTPsum(newTPch) & self.CheckTPindividual(newTPch)
            if CheckStatus is True:
                self.newTPch = newTPch
            else:
                self.newTPch = pd.DataFrame(data = np.zeros((nrows2,ncols2)), index = self.pdindex, columns = self.collabels)
                msg = """Sum of changes in probabilities doesn't add upto 0. \n
                            Or Sum of individual changes is not between -1 and +1. \n
                            Data is loaded below. Please correct and press 'Load from Box'"""
                dlg1 = wx.MessageDialog(self,msg,"Error Message",wx.OK)
                dlg1.ShowModal() #Show the messagebox
                dlg1.Destroy() #Destroy the messagebox when finished)

        except Exception as e:
            dlg1 = wx.MessageDialog(self,str(e),"Error Message",wx.OK)
            dlg1.ShowModal() #Show the messagebox
            dlg1.Destroy() #Destroy the messagebox when finished)

    def CheckTPsum(self,changesTP):
        chkTP = changesTP.copy()
        if self.nstates == 2:
            chkTP['p0'] = chkTP['p00'] + chkTP['p01']
            chkTP['p1'] = chkTP['p10'] + chkTP['p11']
            newchkTP = chkTP.loc[:,['p0','p1']].copy().values
        elif self.nstates == 3:
            chkTP['p0'] = chkTP['p00'] + chkTP['p01'] + chkTP['p02']
            chkTP['p1'] = chkTP['p10'] + chkTP['p11'] + chkTP['p12']
            chkTP['p2'] = chkTP['p20'] + chkTP['p21'] + chkTP['p22']
            newchkTP = chkTP.loc[:,['p0','p1','p2']].copy().values
        res = np.isclose(newchkTP,0,atol=0.001)
        if np.all(res) == True:
            return True
        else:
            return False

    def CheckTPindividual(self,changesTP):
        chkTP = changesTP.copy()
        chkTP1 = np.abs(chkTP.values)
        res = (chkTP1 < 1)
        if np.all(res) == True:
            return True
        else:
            return False

    def OnClose(self,event):
       self.Destroy()

#%%
class ABOUT(wx.Panel):
    """ Provide general description """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent = parent,style = wx.BORDER_SUNKEN)
        #self.SetBackgroundColour((135, 206, 250))
        # 135-206-250

#        self.Bind(wx.EVT_PAINT, self.on_paint)
        # create some sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=0, vgap=0)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)

        p = 2

        imageFile = Logo  #os.path.join('D:\\', 'WGicon.png')
        self.logo1 = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.pic1 = wx.StaticBitmap(self, -1, self.logo1,size= (self.logo1.GetWidth(), self.logo1.GetHeight()))
        grid.Add(self.pic1, pos = (p, 0),span = (2,1), flag = wx.ALL, border = 5)

        #Create an static text box calles text0
        self.text0 = wx.StaticText(self,label = "Weather Generator and \nClimate Change Scenario Generator \nfor Climate Risk Assessment")
        font = wx.Font(18,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text0.SetFont(font)
        self.text0.SetForegroundColour((4,171,250)) # set text color
        # Add to the sizer grid # R: 4 G: 171 B: 250
        grid.Add(self.text0, pos = (p, 1),span = (1,5), flag = wx.ALL, border = 5)

        p += 4
        #Create an static text box calles text0
        self.text1 = wx.StaticText(self,label = "(version 0.2.0 Beta)")
        font = wx.Font(14,wx.DEFAULT,wx.ITALIC, wx.BOLD)
        self.text1.SetFont(font)
        self.text1.SetForegroundColour((4,171,250)) # set text color
        # Add to the sizer grid
        grid.Add(self.text1, pos = (p, 1),span=(1,4), flag = wx.ALL, border = 5)

        p += 4
        #Create an static text box calles text0
        self.text2 = wx.StaticText(self,label = "Developed by:")
        font = wx.Font(12,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text2.SetFont(font)
        self.text2.SetForegroundColour((4,171,250)) # set text color
        # Add to the sizer grid
        grid.Add(self.text2, pos = (p, 1), flag = wx.ALL, border = 5)

        p +=1
        #Create an static text box calles text0
        self.text3 = wx.StaticText(self,label = "Dibesh Shrestha \nDivas B. Basnyat")
        #self.text3 = wx.StaticText(self,label = "Dibesh Shrestha \nDivas B. Basnyat, Ph.D \nWater and Climate Team \nNepal Development Research Institute")
        font = wx.Font(12,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text3.SetFont(font)
        self.text3.SetForegroundColour((4,171,250)) # set text color
        # Add to the sizer grid
        grid.Add(self.text3, pos = (p, 1),span =(1,5), flag = wx.ALL, border = 5)

        p += 2
        #Create an static text box calles text0
        self.text2A = wx.StaticText(self,label = "")
        font = wx.Font(12,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text2A.SetFont(font)
        self.text2A.SetForegroundColour((4,171,250)) # set text color
        # Add to the sizer grid
        grid.Add(self.text2A, pos = (p, 1), flag = wx.ALL, border = 5)

        p +=1
        #Create an static text box calles text0
        self.text3A = wx.StaticText(self,label = "")
        #self.text3 = wx.StaticText(self,label = "Dibesh Shrestha \nDivas B. Basnyat, Ph.D \nWater and Climate Team \nNepal Development Research Institute")
        font = wx.Font(12,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text3A.SetFont(font)
        self.text3A.SetForegroundColour((4,171,250)) # set text color
        # Add to the sizer grid
        grid.Add(self.text3A, pos = (p, 1),span =(1,5), flag = wx.ALL, border = 5)

        p +=2
        imageFile = LogoNDRI  #os.path.join('D:\\', 'WGicon.png')
        self.logo2 = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.pic2 = wx.StaticBitmap(self, -1, self.logo2,size= (self.logo2.GetWidth(), self.logo2.GetHeight()))
        grid.Add(self.pic2, pos = (p, 1), flag = wx.ALL, border = 5)

        #Create an static text box calles text0
        self.text4 = wx.StaticText(self,label = "Nepal Development Research Institute")
        font = wx.Font(14,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text4.SetFont(font)
        self.text4.SetForegroundColour((4,171,250)) # set text color
        # Add to the sizer grid
        grid.Add(self.text4, pos = (p, 2), flag = wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 5)

        p +=2
        #Create an static text box calles text0
        self.text5 = wx.StaticText(self,label = "update (version2) supported by")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text5.SetFont(font)
        self.text5.SetForegroundColour((4,171,250)) # set text color
        # Add to the sizer grid
        grid.Add(self.text5, pos = (p, 1),span =(1,5), flag = wx.ALL, border = 5)

        p +=1
        imageFile = LogoAPN  #os.path.join('D:\\', 'WGicon.png')
        self.logo2 = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.pic2 = wx.StaticBitmap(self, -1, self.logo2,size= (self.logo2.GetWidth(), self.logo2.GetHeight()))
        grid.Add(self.pic2, pos = (p, 1), flag = wx.ALL, border = 5)

        #Create an static text box calles text0
        self.text6 = wx.StaticText(self,label = "Asia Pacific Network")
        font = wx.Font(14,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text6.SetFont(font)
        self.text6.SetForegroundColour((4,171,250)) # set text color
        # Add to the sizer grid
        grid.Add(self.text6, pos = (p, 2), flag = wx.ALL|wx.ALIGN_CENTER_VERTICAL, border = 5)

        hSizer.Add(grid, 1, flag = wx.ALL|wx.EXPAND, border = 5)
        mainSizer.Add(hSizer, 0, wx.ALL, 5)
        self.SetSizerAndFit(mainSizer)
        self.Fit()

#    def on_paint(self, event):
#        # establish the painting canvas
#        dc = wx.PaintDC(self)
#        x = 0
#        y = 0
#        w, h = self.GetSize()
#        dc.GradientFillLinear((x, y, w, h), 'white', 'blue')
#%%
class DESCRIPTION(wx.Panel):
    """ Provide general description """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent = parent,style = wx.BORDER_SUNKEN)
        #self.SetBackgroundColour((135, 206, 250))
        # 135-206-250

        #self.Bind(wx.EVT_PAINT, self.on_paint)
        # create some sizers
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.descrip = wx.TextCtrl(self,size = (200,-1), style = wx.TE_MULTILINE|wx.TE_READONLY|wx.BORDER_NONE)
        text = """\n‘Weather Generator and Climate Change Scenario Generator for Climate Risk Assessment (version 0.1.0 Beta)’ is a tool aiming to support climate risk assessments.\nIt is mainly designed to produce inputs for climate stress test and it provides an interfaces for weather generating process and enforcing changes in climatic means to produce climate change scenarios.
        \nThe tool is developed based on following research papers –
        \nApipattanavis, S., G. Podesta´, B. Rajagopalan, and R. W. Katz (2007), A semiparametric multivariate and multisite weather generator, Water Resour. Res., 43, W11401, doi:10.1029/2006WR005714
        \nSteinschneider, S., and C. Brown (2013), A semiparametric multivariate, multisite weather generator with low-frequency variability for use in climate risk assessments, Water Resour. Res., 49, 7205–7220, doi:10.1002/wrcr.20528.
        \nThere are five major interfaces in this tool.
Interface ‘Annual Series Simulator’ provides tools to generate annual precipitation series based on historic precipitation series by using ARMA method, unlike wavelet based approach as described by Steinschneider and Brown (2013).
Interfaces ‘WG-CRA’ and ‘k-NN WG’ are for weather generation. The former one is conditioned on annual precipitation series as described in Steinschneider and Brown (2013) whereas latter is not conditioned but simply weather generator as formulated in Apipattanavis et al (2007).
Interface ‘CC Scenario Generator’ allows to enforce shifts or changes in distributional properties of weather variables by quantile mapping approach for precipitation and simple shifting approach for other variables and it is described in Steinschneider and Brown (2013).
Finally, interface ‘Result viewer’ is for graphically viewing the results generated by mentioned interfaces.
        \nThis tool is developed in Python 3.7.
        \nPlease feel free to use the tool with acknowledgement and send us email for queries, bugs or issues related to this tool.
        \nRegards,\nDibesh Shrestha, Email: dibeshshrestha@live.com\nDivas B. Basnyat, Ph.D, Email: divas@ndri.org.np\nNepal Development Research Institute\nLalitpur,Nepal\nAugust, 2019

        """
        self.descrip.SetValue(text)
        self.mainSizer.Add(self.descrip,1,wx.ALL|wx.EXPAND, border = 5)

        self.SetSizer(self.mainSizer)
        self.Fit()

#%%
class KnnWG(wx.Panel):
    """k-NN based multisite weatther generator"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent = parent,style = wx.BORDER_SUNKEN)
        #self.SetBackgroundColour((135, 206, 250))
        # These are variables for k-NN simulation
        self.MainData = None
        self.selectedVarList = None
        self.path_to_variables = []
        self.precipitation_column = None
        self.no_simulations = 1 #Default
        self.variable_files = {} #Default
        self.nStates = 3 #Default
        self.wet_threshold = 0.1
        self.extreme_threshold = 0.8
        self.windowsize = 15
        self.weights_method = None
        self.weights = None
        self.initial_pstate = None
        self.initialWV = None
        self.OutputDir = None
        self.originalTP = None
        self.changes_in_TP = None
        self.newTP = None

        # create some sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=0, vgap=0)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)

        # grid position counter, Now working in level 0
        p = 0

        #Create an static text box calles text0
        self.text0 = wx.StaticText(self,label = "INPUTS")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text0.SetFont(font)
        self.text0.SetForegroundColour((0,0,255)) # set text color
        # Add to the sizer grid
        grid.Add(self.text0, pos = (p, 0), flag = wx.ALL, border = 5)

        p += 1

        #Create an button to load main data
        self.B0 = wx.Button(self,label = "Load Main Data ")
        # Add to the sizer grid
        grid.Add(self.B0, pos = (p, 0), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.B0.Bind(wx.EVT_BUTTON,self.LoadMainData)

        #Create an static text box calles text0
        self.MainDataPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.MainDataPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)

        #Create an button to select varaibles
        self.SelectVarsButton = wx.Button(self,label = 'Select Variables')
        grid.Add(self.SelectVarsButton, pos = (p,2), flag = wx.ALL, border = 5)
        self.SelectVarsButton.Bind(wx.EVT_BUTTON,self.SelectVars)

        p += 1

        # Create an static text box named text for declaring precipitation column
        self.textprecip = wx.StaticText(self, label = "Select Precipitation column")
        grid.Add(self.textprecip, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating choices
        choices1 = [] #This is the states for number of states
        self.combo_precip_declare = wx.ComboBox(self,id=wx.ID_ANY,choices = choices1, \
                                                    style = wx.LB_SINGLE)
        grid.Add(self.combo_precip_declare, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo_precip_declare.Bind(wx.EVT_COMBOBOX, self.Oncombo_precip_declare)

        #Create an button to set path to multisite variables files
        self.PathVarsFileButton = wx.Button(self,label = 'Load Variable Files')
        grid.Add(self.PathVarsFileButton, pos = (p,2), flag = wx.ALL, border = 5)
        self.PathVarsFileButton.Bind(wx.EVT_BUTTON,self.PathandLoadVarsFile)

        p += 1

        #Create an static text box calles text0
        self.text99 = wx.StaticText(self,label = "MODEL PARAMETERS")
        self.text99.SetFont(font)
        self.text99.SetForegroundColour((0,0,255))
        grid.Add(self.text99, pos = (p, 0), flag = wx.ALL, border = 5)

        p += 1

        # Create an static text box named text for number of states
        self.text1 = wx.StaticText(self, label = "Number of states")
        grid.Add(self.text1, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating number of states list box
        self.state_list = ['2','3'] #This is the states for number of states
        self.combo1 = wx.ComboBox(self,id=wx.ID_ANY,value = "3",choices = self.state_list, style = wx.LB_SINGLE)
        grid.Add(self.combo1, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo1.Bind(wx.EVT_COMBOBOX, self.OnCombo)

        p += 1

        # Create an static text box named text for number of states
        self.sbox_wet = wx.StaticText(self, label= "Wet Threshold")
        grid.Add(self.sbox_wet, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creading the wet threshold box
        self.WetThresholdBox = wx.lib.masked.numctrl.NumCtrl(self,value = 0.1, \
                               style = wx.TE_PROCESS_ENTER, \
                               integerWidth = 3, fractionWidth=2, \
                               min = 0.0, max = 100.0, limited = 1,\
                               allowNegative=False, allowNone = True)
        grid.Add(self.WetThresholdBox, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.WetThresholdBox.Bind(wx.EVT_TEXT_ENTER,self.OnWetThresholdBox)
        self.WetThresholdBox.Bind(wx.EVT_TEXT,self.OnWetThresholdBox)

        # Create an static text box named text for number of states
        self.sbox_extreme = wx.StaticText(self, label= "Extreme Threshold")
        grid.Add(self.sbox_extreme, pos = (p, 2), flag = wx.ALL, border = 5)

        # Creading the wet threshold box
        self.ExtremeThresholdBox = wx.lib.masked.numctrl.NumCtrl(self,value = 0.8, \
                               style = wx.TE_PROCESS_ENTER, \
                               integerWidth = 1, fractionWidth=2, \
                               min = 0.0, max = 1.0, limited = 1,\
                               allowNegative=False, allowNone = True)
        grid.Add(self.ExtremeThresholdBox, pos = (p, 3), flag = wx.ALL|wx.EXPAND, border = 5)
        self.ExtremeThresholdBox.Bind(wx.EVT_TEXT_ENTER,self.OnExtremeThresholdBox)
        self.ExtremeThresholdBox.Bind(wx.EVT_TEXT,self.OnExtremeThresholdBox)

        p += 1

        # Create an static text box named text for number of states
        self.sbox_window = wx.StaticText(self, label= "Moving Window Size")
        grid.Add(self.sbox_window, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating box for setting moving window size
        self.Mov_win_Box = wx.lib.intctrl.IntCtrl(self,value = 15, \
                              style = wx.TE_PROCESS_ENTER, min = 7, max = 61, \
                              limited = 0)
        grid.Add(self.Mov_win_Box, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.Mov_win_Box.Bind(wx.EVT_TEXT_ENTER,self.OnMov_win_Box)
        self.Mov_win_Box.Bind(wx.EVT_TEXT,self.OnMov_win_Box)

        # Create an static text box for display selecting weights method
        self.sbox_weights = wx.StaticText(self, label= "Assign weights by ")
        grid.Add(self.sbox_weights, pos = (p, 2), flag = wx.ALL, border = 5)

        # Creating number of states list box
        self.weights_method_list = ["equal","user_defined","inv_std"] #This is the states for number of states
        self.WeightsCombo = wx.ComboBox(self,id=wx.ID_ANY, \
                                        choices = self.weights_method_list, \
                                        style = wx.LB_SINGLE)
        grid.Add(self.WeightsCombo, pos = (p, 3), flag = wx.ALL|wx.EXPAND, border = 5)
        self.WeightsCombo.Bind(wx.EVT_COMBOBOX, self.OnWeightsCombo)
        #print(self.weights)

        p += 1

        #Create an static text box calles text0
        self.text2a = wx.StaticText(self,label = "Transition probability")
        # Add to the sizer grid
        grid.Add(self.text2a, pos = (p, 0), flag = wx.ALL, border = 5)

        self.TP_view = wx.Button(self, label = "View")
        grid.Add(self.TP_view, pos = (p, 1), flag = wx.ALL, border = 5)
        self.TP_view.Bind(wx.EVT_BUTTON,self.OnTPview)

        self.TP_change = wx.Button(self, label = "Change")
        grid.Add(self.TP_change, pos = (p, 2), flag = wx.ALL, border = 5)
        self.TP_change.Bind(wx.EVT_BUTTON,self.OnTPchange)

        p += 1

        #Create an static text box calles text0
        self.text2 = wx.StaticText(self,label = "INITIAL CONDITIONS")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text2.SetFont(font)
        self.text2.SetForegroundColour((0,0,255)) # set text color
        # Add to the sizer grid
        grid.Add(self.text2, pos = (p, 0), flag = wx.ALL, border = 5)

        p += 1
        # Create an static text box named text for number of states
        self.text3 = wx.StaticText(self, label = "Precipitation State")
        grid.Add(self.text3, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating number of states list box
        self.istate_list = ['0','1','2']
        self.combo2 = wx.ComboBox(self,id=wx.ID_ANY,value = "",choices = self.istate_list, style = wx.LB_SINGLE)
        grid.Add(self.combo2, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo2.Bind(wx.EVT_COMBOBOX, self.OnCombo2)

        self.WVButton = wx.Button(self, label = "Weather variables")
        grid.Add(self.WVButton, pos = (p, 2), flag = wx.ALL, border = 5)
        self.WVButton.Bind(wx.EVT_BUTTON,self.OnWVButton)

        p += 1

        #Create an static text box
        self.text4 = wx.StaticText(self,label = "SIMULATION")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text4.SetFont(font)
        self.text4.SetForegroundColour((0,0,255)) # set text color
        # Add to the sizer grid
        grid.Add(self.text4, pos = (p, 0), flag = wx.ALL, border = 5)

        p += 1
        # Create an static text box named text
        self.text = wx.StaticText(self, label = "Number of simulations")
        grid.Add(self.text, pos = (p, 0), flag = wx.ALL, border = 5)

        # Create an TextCrtl to supply the answet to number of simulations
        self.nsimBox = wx.lib.intctrl.IntCtrl(self,value = 1, style = wx.TE_PROCESS_ENTER,min = 1, max = 100, limited = 1)
        grid.Add(self.nsimBox, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.nsimBox.Bind(wx.EVT_TEXT_ENTER,self.OnTc)
        self.nsimBox.Bind(wx.EVT_TEXT,self.OnTc)

        p += 1
        # Create an static text box named text simulation date time
        self.text5 = wx.StaticText(self, label = "Start Date")
        grid.Add(self.text5, pos = (p, 0), flag = wx.ALL, border = 5)

        self.SrtDatePickBox = wx.adv.DatePickerCtrl(self)
        self.SrtDatePickBox.SetRange(wx.DateTime.FromDMY(1,1,1900),wx.DateTime.FromDMY(1,1,2101))
        grid.Add(self.SrtDatePickBox, pos = (p,1), flag = wx.ALL|wx.EXPAND, border = 5)
        defDate = self.SrtDatePickBox.GetValue()
        nextdefDate = defDate + wx.DateSpan(days = 1)
        self.SrtDatePickBox.Bind(wx.adv.EVT_DATE_CHANGED,self.checkDate)

        self.text6 = wx.StaticText(self, label = "End Date")
        grid.Add(self.text6, pos = (p, 2), flag = wx.ALL, border = 5)

        self.EndDatePickBox = wx.adv.DatePickerCtrl(self,dt = nextdefDate)
        self.EndDatePickBox.SetRange(wx.DateTime.FromDMY(1,1,1900),wx.DateTime.FromDMY(1,1,2101))
        grid.Add(self.EndDatePickBox, pos = (p,3), flag = wx.ALL|wx.EXPAND, border = 5)
        self.EndDatePickBox.Bind(wx.adv.EVT_DATE_CHANGED,self.checkDate)

        p += 1
        #Create an button to load main data
        self.OutputDirButton = wx.Button(self,label = "Output location ")
        # Add to the sizer grid
        grid.Add(self.OutputDirButton, pos = (p, 0), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.OutputDirButton.Bind(wx.EVT_BUTTON,self.OnOutputDirButton)

        #Create an static text box calles text0
        self.OutputPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.OutputPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)

        p += 1

        self.ResetAll = wx.Button(self,label = "Reset All")
        # Add to the sizer grid
        grid.Add(self.ResetAll, pos = (p, 0), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.ResetAll.Bind(wx.EVT_BUTTON,self.OnResetAll)

        p += 1

        self.SimulateButton = wx.Button(self,label = 'Simulate')
        self.SimulateButton.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, \
                                            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.SimulateButton.SetForegroundColour(wx.Colour(0, 100, 0))
        grid.Add(self.SimulateButton, pos = (p,0), span = (2,2), flag = wx.EXPAND|wx.ALL, border = 5)
        self.SimulateButton.Bind(wx.EVT_BUTTON, self.OnSimulate)

        # Logger to display outputs or processing outputs
        vSizer2 = wx.BoxSizer(wx.VERTICAL)

        self.logger1 = wx.TextCtrl(self,size = (200,-1), style = wx.TE_MULTILINE|wx.TE_READONLY)
        self.logger1.SetInsertionPointEnd()
        #redirect text here
        #redir1=RedirectText(self.logger1)
        #sys.stdout = redir1
        #sys.stderr = redir1
        vSizer2.Add(self.logger1,1,flag = wx.ALL|wx.EXPAND, border = 5)

        #Add clear button to clear the logger text
        self.ClearLoggerButton = wx.Button(self,label = "Clear Logger")
        vSizer2.Add(self.ClearLoggerButton,0,wx.ALL|wx.ALIGN_RIGHT,border = 5)
        self.ClearLoggerButton.Bind(wx.EVT_BUTTON,self.OnClearLogger)

        hSizer.Add(grid, 1, flag = wx.ALL|wx.EXPAND, border = 5)
        hSizer.Add(vSizer2,1,flag = wx.ALL|wx.EXPAND, border = 5)
        mainSizer.Add(hSizer, 0, wx.ALL, 5)
        self.SetSizerAndFit(mainSizer)
        self.Fit()

    def LoadMainData(self,event):
        """Open a file"""
        self.dirname = ''
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        dlg = wx.FileDialog(self, "Choose main data file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            self.MainDataPath.SetValue(f)
            # display this in file control
            MainData = pd.read_csv(f,header = 0,parse_dates=True)
            MainData.index.rename('id',inplace=True)
            MainData.Date = pd.to_datetime(MainData.Date,format="%Y-%m-%d")
            cols=[i for i in MainData.columns if i not in ["Date","date","year","month","day"]]
            for col in cols:
                MainData[col]=pd.to_numeric(MainData[col],errors='coerce')
            # self.control.SetValue(f.read()) #This is showing data on the logger
            self.MainData = MainData
            print("Data loaded and convert into pandas dataframe!")
            print("Its columns are: {}".format(self.MainData.columns))
        dlg.Destroy()

    def SelectVars(self,event):
        """Select the variables"""
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        if self.MainData is None:
            textmsg = """Please load the main data first!"""
            dlg = wx.MessageDialog(self,textmsg,"Variable selection ",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)
        else:
            vlist = list(self.MainData.columns)
            y = VarSelectionFrame(self,title="Select the variables",var_list = vlist)
            y.ShowModal()
            self.selectedVarList = y.selectedVarList
            print("Selected variables are: {}".format(self.selectedVarList))

            # Laoding the varibales into combo box for declaration
            self.combo_precip_declare.Clear()
            for i in self.selectedVarList:
                self.combo_precip_declare.Append(i)

    def PathandLoadVarsFile(self,event):
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        if self.selectedVarList is None:
            textmsg = """Please select the variables first!"""
            dlg = wx.MessageDialog(self,textmsg,"Set path to files",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)
        else:
            y1 = SetPathVariableFilesFrame(self,title = 'Set path to weather variable files', \
                                        sel_var_list = self.selectedVarList)
            y1.ShowModal()
            self.path_to_variables = y1.sel_var_path
            print("Path of variable files are: ")
            print(self.path_to_variables) #This is dictionary
            # Loading the data
            for keys,values in self.path_to_variables.items():
                varfile = pd.read_csv(values,header = 0,parse_dates=True)
                varfile.index.rename('id',inplace=True)
                varfile.Date = pd.to_datetime(varfile.Date, format="%Y-%m-%d")
                cols=[i for i in varfile.columns if i not in ["Date","date","year","month","day"]]
                for col in cols:
                    varfile[col]=pd.to_numeric(varfile[col],errors='coerce')
                print("File {} loaded as {}!".format(values,keys))
                self.variable_files[keys] = varfile

    def Oncombo_precip_declare(self,event):
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        id1 = self.combo_precip_declare.GetSelection()
        self.precipitation_column = self.selectedVarList[id1]
        print("precipitation_column is {}.".format(self.precipitation_column))

    def OnCombo(self, event):
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        nStatesId = self.combo1.GetSelection()
        self.nStates = int(self.state_list[nStatesId])
        if self.nStates == 2:
            self.ExtremeThresholdBox.Disable()
            self.combo2.Clear()
            self.combo2.Append('0')
            self.combo2.Append('1')
        elif self.nStates == 3:
            self.ExtremeThresholdBox.Enable()
            self.combo2.Clear()
            self.combo2.Append('0')
            self.combo2.Append('1')
            self.combo2.Append('2')

    def OnTc(self, event):
        n = int(self.nsimBox.GetLineText(0))
        self.no_simulations = n

    def OnWetThresholdBox(self,event):
        n = float(self.WetThresholdBox.GetLineText(0))
        self.wet_threshold = n
        #print("Wet Threshold set to: {}".format(self.wet_threshold))

    def OnExtremeThresholdBox(self,event):
        n = float(self.ExtremeThresholdBox.GetLineText(0))
        self.extreme_threshold = n
        #print("Extreme Threshold set to: {}".format(self.extreme_threshold))

    def OnMov_win_Box(self,event):
        n = float(self.Mov_win_Box.GetLineText(0))
        self.windowsize = n

    def OnWeightsCombo(self,event):
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        Id = self.WeightsCombo.GetSelection()
        self.weights_method = self.weights_method_list[Id]
        print("Weighing method given to weigh the variables in k-NN is '{}'.".format(self.weights_method))
        if self.weights_method == self.weights_method_list[1]:
            if self.selectedVarList is not None:
                y3 = WeightsFrame(self,title = 'Provide weights', \
                                            sel_var_list = self.selectedVarList,\
                                            precip_var_name = self.precipitation_column,\
                                            nature = 'weights')
                y3.ShowModal()
                self.weights = y3.sel_var_weights
                print("'user_defined' weights set to {}".format(self.weights))
            else:
                textmsg = """Please select the variables first!"""
                dlg = wx.MessageDialog(self,textmsg,"Reminder!",wx.OK)
                dlg.ShowModal() #Show the messagebox
                dlg.Destroy() #Destroy the messagebox when finished)


    def OnTPview(self,event):
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        print("Checking the inputs.....")
        print()
        # Checking one-by-one manually
        ChekupMarkerflag = {}

        if self.MainData is None:
            msgs = 'MainData not loaded.'
            ChekupMarkerflag['MainData'] = (False,msgs,self.MainData)
        else:
            msgs = 'MainData loaded!'
            ChekupMarkerflag['MainData'] = (True,msgs,self.MainData)

        if self.selectedVarList is None:
            msgs ='Variables not yet selected.'
            ChekupMarkerflag['selectedVarList'] = (False,msgs,self.selectedVarList)
        else:
            msgs = 'Variables selected.'
            ChekupMarkerflag['selectedVarList'] = (True,msgs,self.selectedVarList)

        if self.precipitation_column is None:
            msgs = 'precipitation_column not defined!'
            ChekupMarkerflag['precipitation_column'] = (False,msgs,self.precipitation_column)
        else:
            msgs = 'precipitation_column defined!'
            ChekupMarkerflag['precipitation_column'] = (True,msgs,self.precipitation_column)

        for keys,values in ChekupMarkerflag.items():
            if values[0] is False:
                print(values[1])
                print()
            else:
                print(values[1])
                print(values[2])
                print()

        nStatesId = self.combo1.GetSelection()
        self.nStates = int(self.state_list[nStatesId])
        print("Number of precipitation states set to {}".format(self.nStates))

        self.wet_threshold = self.WetThresholdBox.GetValue()
        print("Wet threshold set to {}".format(self.wet_threshold))

        self.extreme_threshold = self.ExtremeThresholdBox.GetValue()
        print("Extreme threshold set to {}".format(self.extreme_threshold))

        Flags = []
        for keys,values in ChekupMarkerflag.items():
            Flags.append(values[0])

        if np.array(Flags).all() == True:
            aWG1 = wg.WeatherDTS(self.MainData, name = 'computeTP', \
                                precipitation_column_name = self.precipitation_column, \
                                var_dict = {})
            # Setting up the model parameters
            aWG1.setNoStates(nostates = self.nStates)
            aWG1.setWetThreshold(wet_threshold_value = self.wet_threshold)
            aWG1.setExtremeThreshold(extreme_threshold_value = self.extreme_threshold)
            self.originalTP = aWG1.getTP().round(3)
            #self.originalTP.to_csv('TP.csv')
            tp_frame1 = TP_Frame_View(self,title ='Transition probability', \
                                 TP =self.originalTP, \
                                 nstates = self.nStates)
            tp_frame1.ShowModal()
            print('Transition Probability Viewed!')
        else:
            print("Cannot compute TP!. Please check the inputs first!")

    def OnTPchange(self,event):
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        try:
            aWG1 = wg.WeatherDTS(self.MainData, name = 'computeTP', \
                                precipitation_column_name = self.precipitation_column, \
                                var_dict = {})
            # Setting up the model parameters
            aWG1.setNoStates(nostates = self.nStates)
            aWG1.setWetThreshold(wet_threshold_value = self.wet_threshold)
            aWG1.setExtremeThreshold(extreme_threshold_value = self.extreme_threshold)
            self.originalTP = aWG1.getTP().round(3)
            tp_frame2 = TP_Frame_Change(self,title ='Transition probability', \
                                 TP =self.originalTP, \
                                 nstates = self.nStates)
            tp_frame2.ShowModal()
            self.changes_in_TP = tp_frame2.newTPch
            self.newTP = self.originalTP + self.changes_in_TP
            print("Changes in transition probability:")
            print("")
            print(self.changes_in_TP)
            print("New transition probability:")
            print("")
            print(self.newTP)

        except Exception as e:
            msg = "Cannot compute TP!. Please check the inputs first! \n"
            print(msg + str(e) )


    def OnCombo2(self, event):
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        nStatesId = self.combo2.GetSelection()
        self.initial_pstate = int(self.istate_list[nStatesId])
        print("Initial precipitation state is {}.".format(self.initial_pstate))

    def OnWVButton(self,event):
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        if self.selectedVarList is not None:
            y4 = WeightsFrame(self,title = 'Provide values', \
                                        sel_var_list = self.selectedVarList, \
                                        precip_var_name = self.precipitation_column,\
                                        nature = 'values')
            y4.ShowModal()
            self.initialWV = y4.sel_var_weights
            print("Intial values of weather variables set to {}".format(self.initialWV))
        else:
            textmsg = """Please select the variables first!"""
            dlg = wx.MessageDialog(self,textmsg,"Reminder!",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)

    def checkDate(self,event):
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        srtDate = self.SrtDatePickBox.GetValue()
        endDate = self.EndDatePickBox.GetValue()
        #print(srtDate.year)
        #print(srtDate.month+1)
        #print(srtDate.day)
        #print(endDate.year)
        #print(endDate.month+1)
        #print(endDate.day)
        #dd = pd.date_range(datetime(srtDate.year,srtDate.month+1,srtDate.day), \
        #                   datetime(endDate.year,endDate.month+1,endDate.day))
        #print(dd)
        if endDate <= srtDate:
            print('Warning: End Date is earlier than Start Date!')

    def OnOutputDirButton(self,event):
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        """Open a file"""
        self.OutputDir = ''
        dlg = wx.DirDialog(self, "Choose output location")
        if dlg.ShowModal() == wx.ID_OK:
            self.OutputDir = dlg.GetPath()
            self.OutputPath.SetValue(self.OutputDir)
        dlg.Destroy()

    def OnResetAll(self,event):
        self.MainData = None
        self.selectedVarList = None
        self.path_to_variables = []
        self.precipitation_column = None
        self.no_simulations = 1 #Default
        self.variable_files = {} #Default
        self.nStates = 3 #Default
        self.wet_threshold = 0.1
        self.extreme_threshold = 0.8
        self.windowsize = 15
        self.weights_method = None
        self.weights = None
        self.initial_pstate = None
        self.initialWV = None
        self.OutputDir = None
        self.originalTP = None
        self.changes_in_TP = None
        self.newTP = None

        self.MainDataPath.SetValue('')
        self.OutputPath.SetValue('')

        self.combo1.SetSelection(1)
        self.combo2.SetSelection(-1)
        self.WeightsCombo.SetSelection(-1)
        self.combo_precip_declare.Clear()
        self.WetThresholdBox.SetValue(0.1)
        self.ExtremeThresholdBox.SetValue(0.8)
        self.Mov_win_Box.SetValue(15)
        self.nsimBox.SetValue(1)

        if self.nStates == 3:
            self.ExtremeThresholdBox.Enable()
            self.combo2.Clear()
            self.combo2.Append('0')
            self.combo2.Append('1')
            self.combo2.Append('2')

        self.logger1.SetValue("")

    def OnSimulate(self,event):
        sys.stdout = self.logger1
        sys.stderr = self.logger1
        print("Checking the inputs.....")
        print()
        # Checking one-by-one manually
        ChekupMarkerflag = {}

        if self.MainData is None:
            msgs = 'MainData not loaded.'
            ChekupMarkerflag['MainData'] = (False,msgs,self.MainData)
        else:
            msgs = 'MainData loaded!'
            ChekupMarkerflag['MainData'] = (True,msgs,self.MainData)

        if self.selectedVarList is None:
            msgs ='Variables not yet selected.'
            ChekupMarkerflag['selectedVarList'] = (False,msgs,self.selectedVarList)
        else:
            msgs = 'Variables selected.'
            ChekupMarkerflag['selectedVarList'] = (True,msgs,self.selectedVarList)

        if len(self.path_to_variables) == 0:
            msgs = 'Variables path not supplied. \n So, it will redirect to single site generation!'
            #This one is still set as True as it will redirect to single site generation
            ChekupMarkerflag['path_to_variables'] = (True,msgs,self.path_to_variables)
        else:
            msgs = 'Variables path selected. \n So, it will redirect to multisite generation!'
            ChekupMarkerflag['path_to_variables'] = (True,msgs,self.path_to_variables)

        if len(self.variable_files) == 0:
            msgs = 'Variable files not supplied. \n So, it will redirect to single site generation!'
            #This one is still set as True as it will redirect to single site generation
            ChekupMarkerflag['variable_files'] = (True,msgs,self.variable_files)
        else:
            msgs = 'Variables files supplied. \n So, it will redirect to multisite generation!'
            ChekupMarkerflag['variable_files'] = (True,msgs,self.variable_files)

        if self.weights_method is None:
            msgs = 'Method for weights is not yet supplied!'
            ChekupMarkerflag['weights_method'] = (False,msgs,self.weights_method)
        else:
            msgs = 'Method for weights is supplied!'
            ChekupMarkerflag['weights_method'] = (True,msgs,self.weights_method)

        if self.weights_method == 'user_defined':
            if self.weights is None:
                msgs = 'Weights is not yet supplied!'
                ChekupMarkerflag['weights'] = (False,msgs,self.weights_method)
            else:
                msgs = 'Weights supplied!'
                ChekupMarkerflag['weights'] = (True,msgs,self.weights_method)

        if self.initial_pstate is None:
            msgs = 'Intial state for precipitation is not yet set!'
            ChekupMarkerflag['initial_pstate'] = (False,msgs,self.initial_pstate)
        else:
            msgs = 'Intial state for precipitation is set!'
            ChekupMarkerflag['initial_pstate'] = (True,msgs,self.initial_pstate)

        if self.initialWV is None:
            msgs = 'Intial weather vectors is not yet set!'
            ChekupMarkerflag['initialWV'] = (False,msgs,self.initialWV)
        else:
            msgs = 'Intial weather vectors is set!'
            ChekupMarkerflag['initialWV'] = (True,msgs,self.initialWV)

        # Checking Simulation Date tile
        sD = self.SrtDatePickBox.GetValue()
        print(sD.year)
        print(sD.month)
        eD = self.EndDatePickBox.GetValue()
        if eD <= sD:
            msgs = 'Warning: End Date is earlier than Start Date!'
            ChekupMarkerflag['checkDate'] = (False,msgs,[sD,eD])
        else:
            msgs = 'Simulation dates set!'
            ChekupMarkerflag['checkDate'] = (True,msgs,[sD,eD])

        for keys,values in ChekupMarkerflag.items():
            if values[0] is False:
                print(values[1])
                print()
            else:
                print(values[1])
                print(values[2])
                print()

        if self.OutputDir is None:
            msgs = 'Output directory is not yet set. So, setting it to current working directory!'
            self.OutputDir = os.getcwd();
            print(msgs)

        # Getting the values from the boxes
        self.no_simulations = self.nsimBox.GetValue()
        print("Number of simulations set to {}".format(self.no_simulations))

        nStatesId = self.combo1.GetSelection()
        self.nStates = int(self.state_list[nStatesId])
        print("Number of precipitation states set to {}".format(self.nStates))

        self.wet_threshold = self.WetThresholdBox.GetValue()
        print("Wet threshold set to {}".format(self.wet_threshold))

        self.extreme_threshold = self.ExtremeThresholdBox.GetValue()
        print("Extreme threshold set to {}".format(self.extreme_threshold))

        self.windowsize = self.Mov_win_Box.GetValue()
        print("windowsize set to {}".format(self.windowsize))

        Flags = []
        for keys,values in ChekupMarkerflag.items():
            Flags.append(values[0])

        store_results = {}  # Will store based on the number of simulations
                            # starting from 1
        if np.array(Flags).all() == True:
            print()
            print()
            for i in range(1,self.no_simulations+1):
                print("Setting up the model for simulation no {}.".format(i))
                # Creating the class of WeatherDTS using wg module
                sim_name = 'Simulation_' + str(i)
                aWG = wg.WeatherDTS(self.MainData, name = sim_name, \
                                    precipitation_column_name = self.precipitation_column, \
                                    var_dict = self.variable_files)
                # Setting up the model parameters
                aWG.setNoStates(nostates = self.nStates)
                aWG.setWetThreshold(wet_threshold_value = self.wet_threshold)
                aWG.setExtremeThreshold(extreme_threshold_value = self.extreme_threshold)
                aWG.getTP()
                #print('Original TP')
                #print(aWG.getTP())
                # Use the user-defined transition probabilities if provided
                if self.newTP is not None:
                    aWG.setTP(self.newTP)
                #print('USED TP')
                #print(aWG.getTP())
                # else use the original one (so doesn't have to do anything)
                #aWG.arrangeMovingWindow(windowsize = self.windowsize)
                sim_date_series = pd.date_range(datetime(sD.year,sD.month+1,sD.day),\
                                                datetime(eD.year,eD.month+1,eD.day))
                outdir = os.path.join(self.OutputDir,'OUTPUT')
                if not os.path.exists(outdir):
                    os.mkdir(outdir)

                print('Output will be created in:')
                print(outdir)
                print()

                if self.weights_method != 'user_defined':
                    wts = []
                else:
                    wts = self.weights

                print('Simulation started....!')
                time.sleep(2)
                aWG.simulate_kNN(simulation_dateseries = sim_date_series,\
                                 iState = self.initial_pstate,\
                                 initialWV = self.initialWV, \
                                 columnsWV = self.selectedVarList,\
                                 windowsize = self.windowsize,\
                                 messages = False,\
                                 weights_method = self.weights_method,\
                                 writefile = True, \
                                 outputdir = outdir,\
                                 weights = wts)
                #simulate_kNN(self,simulation_dateseries,iState,initialWV,\
                # columnsWV,windowsize=7,messages = False,weights_method = 'inv_std',\
                # writefile = False,outputdir = os.getcwd(), **kwargs):
                store_results[i] = aWG

                print("{} completed.".format(sim_name))

        else:
            textmsg = """Please check missing or errorneous inputs!"""
            dlg = wx.MessageDialog(self,textmsg,"Reminder",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)

    def OnClearLogger(self,event):
        self.logger1.SetValue("")
#%%
###-----------------------------------###-----------------------------------###
class CCSG(wx.Panel):
    """Climate Change Scenario Simulator"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent,style = wx.BORDER_SUNKEN)
        # These are variables for k-NN simulation
        self.MainData = None
        self.selectedVarList = None
        self.path_to_variables = []
        self.precipitation_column = None
        self.variable_files = {} #Default
        self.changes_params = {}
        self.wet_threshold = 0.1
        self.OutputDir = None
        self.changes_files_to_save = None

        # create some sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=0, vgap=0)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)

        # grid position counter, Now working in level 0
        p = 0

        #Create an static text box calles text0
        self.text0 = wx.StaticText(self,label = "INPUTS")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text0.SetFont(font)
        self.text0.SetForegroundColour((0,0,255)) # set text color
        # Add to the sizer grid
        grid.Add(self.text0, pos = (p, 0), flag = wx.ALL, border = 5)

        p += 1

        #Create an button to load main data
        self.B0 = wx.Button(self,label = "Load Main Data ")
        # Add to the sizer grid
        grid.Add(self.B0, pos = (p, 0), flag = wx.ALL|wx.EXPAND, border = 5)
        # Add the binder to LoadMainData
        self.B0.Bind(wx.EVT_BUTTON,self.LoadMainData)

        #Create an static text box calles text0
        self.MainDataPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.MainDataPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)

        #Create an button to select varaibles
        self.SelectVarsButton = wx.Button(self,label = 'Select Variables')
        grid.Add(self.SelectVarsButton, pos = (p,2), flag = wx.ALL|wx.EXPAND, border = 5)
        self.SelectVarsButton.Bind(wx.EVT_BUTTON,self.SelectVars)

        p += 1

        # Create an static text box named text for declaring precipitation column
        self.textprecip = wx.StaticText(self, label = "Select Precipitation")
        grid.Add(self.textprecip, pos = (p, 0), flag = wx.ALL|wx.EXPAND, border = 5)

        # Creating choices
        choices1 = [] #This is the states for number of states
        self.combo_precip_declare = wx.ComboBox(self,id=wx.ID_ANY,choices = choices1, \
                                                    style = wx.LB_MULTIPLE)
        grid.Add(self.combo_precip_declare, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo_precip_declare.Bind(wx.EVT_COMBOBOX, self.Oncombo_precip_declare)

        #Create an button to set path to multisite variables files
        self.PathVarsFileButton = wx.Button(self,label = 'Load Variable Files')
        grid.Add(self.PathVarsFileButton, pos = (p,2), flag = wx.ALL|wx.EXPAND, border = 5)
        self.PathVarsFileButton.Bind(wx.EVT_BUTTON,self.PathandLoadVarsFile)

        p += 1

        #Create an static text box calles text0
        self.text99 = wx.StaticText(self,label = "PARAMETERS")
        self.text99.SetFont(font)
        self.text99.SetForegroundColour((0,0,255))
        grid.Add(self.text99, pos = (p, 0), flag = wx.ALL|wx.EXPAND, border = 5)

        # Create an static text box named text for Wet Threshold
        self.sbox_wet = wx.StaticText(self, label= "Wet Threshold")
        grid.Add(self.sbox_wet, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)

        # Creading the wet threshold box
        self.WetThresholdBox = wx.lib.masked.numctrl.NumCtrl(self,value = 0.1, \
                               style = wx.TE_PROCESS_ENTER, \
                               integerWidth = 3, fractionWidth=2, \
                               min = 0.0, max = 100.0, limited = 1,\
                               allowNegative=False, allowNone = True)
        grid.Add(self.WetThresholdBox, pos = (p, 2), flag = wx.ALL|wx.EXPAND, border = 5)
        self.WetThresholdBox.Bind(wx.EVT_TEXT_ENTER,self.OnWetThresholdBox)
        self.WetThresholdBox.Bind(wx.EVT_TEXT,self.OnWetThresholdBox)

        p += 1
        #Create an static text box
        self.text100 = wx.StaticText(self,label = "CC PARAMETERS")
        self.text100.SetFont(font)
        self.text100.SetForegroundColour((0,0,255))
        grid.Add(self.text100, pos = (p, 0), flag = wx.ALL, border = 5)

        p += 1
        #Create an button to set path to multisite variables files
        self.ChangesFileButton = wx.Button(self,label = 'Load parameters from file')
        grid.Add(self.ChangesFileButton, pos = (p,0), flag = wx.ALL|wx.ALIGN_LEFT, border = 5)
        self.ChangesFileButton.Bind(wx.EVT_BUTTON,self.PathandLoadChangesFile)
        #self.ChangesFileButton.Disable()

        p += 1
        # Creating the grid box
        self.chGrid = gridlib.Grid(self,size = (450,280))
        self.chGrid.CreateGrid(12,10)
        for j in range(0,10):
            self.chGrid.SetColLabelValue(j,str(j))
        for i in range(12):
            self.chGrid.SetRowLabelValue(i,calendar.month_abbr[i+1])

        grid.Add(self.chGrid, pos = (p,0),span = (1,5), flag = wx.ALL|wx.EXPAND, border = 5)
        self.chGrid.Disable()

        p += 1
        self.loadchanges_box = wx.Button(self,label = 'Load parameters(Box)')
        grid.Add(self.loadchanges_box, pos = (p,0), flag = wx.ALL|wx.ALIGN_LEFT, border = 5)
        self.loadchanges_box.Bind(wx.EVT_BUTTON,self.OnLoadChangesFromBox)

        self.savechanges_box = wx.Button(self,label = 'Save parameters')
        grid.Add(self.savechanges_box, pos = (p,1), flag = wx.ALL|wx.ALIGN_LEFT, border = 5)
        self.savechanges_box.Bind(wx.EVT_BUTTON,self.OnSaveChanges)

        self.ResetAllButton = wx.Button(self,label = 'Reset All')
        grid.Add(self.ResetAllButton, pos = (p,2), flag = wx.ALL|wx.ALIGN_LEFT, border = 5)
        self.ResetAllButton.Bind(wx.EVT_BUTTON,self.OnResetAll)

        p += 1
        #Create an button to load main data
        self.OutputDirButton = wx.Button(self,label = "Output location ")
        # Add to the sizer grid
        grid.Add(self.OutputDirButton, pos = (p, 0), flag = wx.ALL|wx.EXPAND|wx.ALIGN_LEFT, border = 5)
        # Add the binder to LoadMainData
        self.OutputDirButton.Bind(wx.EVT_BUTTON,self.OnOutputDirButton)

        #Create an static text box calles text0
        self.OutputPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.OutputPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)


        self.GenerateButton = wx.Button(self,label = 'Apply Changes')
        self.GenerateButton.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, \
                                            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.GenerateButton.SetForegroundColour(wx.Colour(0, 100, 0))
        grid.Add(self.GenerateButton, pos = (p,2), span = (1,3), flag = wx.EXPAND|wx.ALL, border = 5)
        self.GenerateButton.Bind(wx.EVT_BUTTON, self.OnGenerate)

        p += 1
        # Logger to display outputs or processing outputs
        vSizer2 = wx.BoxSizer(wx.VERTICAL)

        self.logger = wx.TextCtrl(self, size = (200,-1), style = wx.TE_MULTILINE|wx.TE_READONLY)
        self.logger.SetInsertionPointEnd()
        # redirect text here
#        redir2=RedirectText(self.logger)
#        sys.stdout = redir2
#        sys.stderr = redir2
        vSizer2.Add(self.logger,1,flag = wx.ALL|wx.EXPAND, border = 5)

        #Add clear button to clear the logger text
        self.ClearLoggerButton = wx.Button(self,label = "Clear Logger")
        vSizer2.Add(self.ClearLoggerButton,0,wx.ALL|wx.ALIGN_RIGHT,border = 5)
        self.ClearLoggerButton.Bind(wx.EVT_BUTTON,self.OnClearLogger)

        hSizer.Add(grid, 1, flag = wx.ALL|wx.EXPAND, border = 5)
        hSizer.Add(vSizer2,1,flag = wx.ALL|wx.EXPAND, border = 5)
        mainSizer.Add(hSizer, 0, wx.ALL, 5)
        self.SetSizerAndFit(mainSizer)
        self.Fit()

    def LoadMainData(self,event):
        sys.stdout = self.logger
        sys.stderr = self.logger
        """Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose main data file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            self.MainDataPath.SetValue(f)
            # display this in file control
            MainData = pd.read_csv(f,header = 0,parse_dates=True)
            MainData.index.rename('id',inplace=True)
            MainData.Date = pd.to_datetime(MainData.Date,format="%Y-%m-%d")
            cols=[i for i in MainData.columns if i not in ["Date","date","year","month","day"]]
            for col in cols:
                MainData[col]=pd.to_numeric(MainData[col],errors='coerce')
            # self.control.SetValue(f.read()) #This is showing data on the logger
            self.MainData = MainData
            print("Data loaded and convert into pandas dataframe!")
            print("Its columns are: {}".format(self.MainData.columns))
        dlg.Destroy()

    def SelectVars(self,event):
        sys.stdout = self.logger
        sys.stderr = self.logger
        """Select the variables"""
        if self.MainData is None:
            textmsg = """Please load the main data first!"""
            dlg = wx.MessageDialog(self,textmsg,"Variable selection ",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)
        else:
            vlist = list(self.MainData.columns)
            y = VarSelectionFrame(self,title="Select the variables",var_list = vlist)
            y.ShowModal()
            self.selectedVarList = y.selectedVarList
            print("Selected variables are: {}".format(self.selectedVarList))
            #Loading the varibales into combo box for declaration
            self.combo_precip_declare.Clear()
            for i in self.selectedVarList:
                self.combo_precip_declare.Append(i)
            self.UpdateGrid()

    def Oncombo_precip_declare(self,event):
        sys.stdout = self.logger
        sys.stderr = self.logger
        id1 = self.combo_precip_declare.GetSelection()
        self.precipitation_column = self.selectedVarList[id1]
        print("precipitation_column is {}.".format(self.precipitation_column))
        self.UpdateGrid()

    def PathandLoadVarsFile(self,event):
        sys.stdout = self.logger
        sys.stderr = self.logger
        if self.selectedVarList is None:
            textmsg = """Please select the variables first!"""
            dlg = wx.MessageDialog(self,textmsg,"Set path to files",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)
        else:
            y1 = SetPathVariableFilesFrame(self,title = 'Set path to weather variable files', \
                                        sel_var_list = self.selectedVarList)
            y1.ShowModal()
            self.path_to_variables = y1.sel_var_path
            print("Path of variable files are: ")
            print(self.path_to_variables) #This is dictionary
            # Loading the data
            for keys,values in self.path_to_variables.items():
                varfile = pd.read_csv(values,header = 0,parse_dates=True)
                varfile.index.rename('id',inplace=True)
                varfile.Date = pd.to_datetime(varfile.Date, format="%Y-%m-%d")
                cols=[i for i in varfile.columns if i not in ["Date","date","year","month","day"]]
                for col in cols:
                    varfile[col]=pd.to_numeric(varfile[col],errors='coerce')
                print("File {} loaded as {}!".format(values,keys))
                self.variable_files[keys] = varfile

    def PathandLoadChangesFile(self,event):
        sys.stdout = self.logger
        sys.stderr = self.logger
        if self.selectedVarList is None:
            textmsg = """Please select the variables first!"""
            dlg = wx.MessageDialog(self,textmsg,"Set path to files",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)
        else:
            y1 = SetPathVariableFilesFrame(self,title = 'Set path to climate change parameter files', \
                                        sel_var_list = self.selectedVarList)
            y1.ShowModal()
            self.path_to_variables = y1.sel_var_path
            print("Path of changes files are: ")
            print(self.path_to_variables) #This is dictionary
            # Loading the data
            for keys,values in self.path_to_variables.items():
                varfile = pd.read_csv(values,header = 0,parse_dates=True,index_col = 0)
                self.changes_params[keys] = varfile.values.T.tolist()
                print('File:')
                print(varfile)
                print("Parameters {} loaded in dictionary with key {}!".format(values,keys))
                print("Changes:")
                print(self.changes_params[keys])

            # Loading the changes into the grid
            ncols = self.chGrid.GetNumberCols()

            col_names = []
            for i in range(ncols):
                col_names.append(self.chGrid.GetColLabelValue(i))

            for keys,values in self.changes_params.items():
                if keys == self.precipitation_column:
                    id1 = col_names.index(keys +'_'+'mean changes (fraction)')
                    id2 = col_names.index(keys +'_'+'CV changes (fraction)')
                    mean_ch = values[0]
                    CV_ch = values[1]
                    for k1 in range(12):
                        self.chGrid.SetCellValue(k1,id1,str(mean_ch[k1]))
                        self.chGrid.SetCellValue(k1,id2,str(CV_ch[k1]))
                else:
                    ch = values[0]
                    id3 = col_names.index(keys+'_'+'mean (value)')
                    for k2 in range(12):
                        self.chGrid.SetCellValue(k2,id3,str(ch[k2]))

    def OnWetThresholdBox(self,event):
        sys.stdout = self.logger
        sys.stderr = self.logger
        n = float(self.WetThresholdBox.GetLineText(0))
        self.wet_threshold = n
        #print("Wet Threshold set to: {}".format(self.wet_threshold))

    def OnLoadChangesFromBox(self,event):
        """ loading the changes made in grid box """
        sys.stdout = self.logger
        sys.stderr = self.logger
        ncols = self.chGrid.GetNumberCols()
        col_names = []
        indexcol = ['Jan','Feb','Mar','Apr','May','Jun',\
                            'Jul','Aug','Sep','Oct','Nov','Dec']
        self.changes_files_to_save = {}
        for i in range(ncols):
            col_names.append(self.chGrid.GetColLabelValue(i))
        for i in self.selectedVarList:
            if self.precipitation_column == i:
                n1 = (i+'_'+'mean changes (fraction)')
                id1 = col_names.index(n1)
                n2 = (i+'_'+'CV changes (fraction)')
                id2 = col_names.index(n2)
                ch_mean = []
                ch_CV = []
                for l1 in range(12):
                    ch_mean.append(float(self.chGrid.GetCellValue(l1,id1)))
                    ch_CV.append(float(self.chGrid.GetCellValue(l1,id2)))

                self.changes_params[i] = [ch_mean,ch_CV]
                X = np.array([ch_mean,ch_CV])
                X = X.T
                self.changes_files_to_save[i] = pd.DataFrame(data = X,index = indexcol,columns =[n1,n2] )
            else:
                n3 = (i+'_'+'mean (value)')
                id3 = col_names.index(n3)
                ch = []
                for l2 in range(12):
                    ch.append(float(self.chGrid.GetCellValue(l2,id3)))
                self.changes_params[i] = [ch]
                Y = np.array([ch])
                Y = Y.T
                self.changes_files_to_save[i] = pd.DataFrame(data = Y,index = indexcol,columns =[n3])
        print(self.changes_files_to_save)
        print(self.changes_params)

    def OnSaveChanges(self,event):
        sys.stdout = self.logger
        sys.stderr = self.logger
        if self.changes_files_to_save is None:
            print("Please press 'Load parameters(Box)' first to load changes from box!")
        else:
            OD = ''
            dlg = wx.DirDialog(self, "Choose output location to save changes file")
            if dlg.ShowModal() == wx.ID_OK:
                OD = dlg.GetPath()
            dlg.Destroy()
            for k1,v1 in self.changes_files_to_save.items():
                fname = 'Changes_' + k1 +'.csv'
                fpath = os.path.join(OD,fname)
                v1.to_csv(fpath)
                print('File saved in {} as {}'.format(fpath,fname))

    def UpdateGrid(self):
        try:
            #self.chGrid.Enable()
            ncols = self.chGrid.GetNumberCols()
            if self.precipitation_column is None:
                nvars = len(self.selectedVarList)
            else:
                nvars = len(self.selectedVarList) + 1
            if (nvars) < ncols:  #plus one beacuse precip has to parameters to chnage
                # Delete unnecessary columns
                self.chGrid.DeleteCols(pos = nvars , numCols = (ncols - nvars))
            else:
                self.chGrid.AppendCols(numCols = nvars - ncols)

            self.x = []
            for i in self.selectedVarList:
                if self.precipitation_column == i:
                    self.x.append(i+'_'+'mean changes (fraction)')
                    self.x.append(i+'_'+'CV changes (fraction)')
                else:
                    self.x.append(i+'_'+'mean (value)')
            for i,j in enumerate(self.x):
                self.chGrid.SetColLabelValue(i,j)
                self.chGrid.AutoSizeColLabelSize(i)
            ncols = self.chGrid.GetNumberCols()
            nrows = self.chGrid.GetNumberRows()
            for rows in range(nrows):
                for cols in range(ncols):
                    self.chGrid.SetCellEditor(rows, cols, \
                                              gridlib.GridCellFloatEditor(width = 6, precision = 2))
                    self.chGrid.SetCellValue(rows,cols,'0.00')
            self.chGrid.Enable()
        except:
            if self.selectedVarList is None:
                textmsg = """Please select the variables first!"""
                dlg = wx.MessageDialog(self,textmsg,"Variable selection ",wx.OK)
                dlg.ShowModal() #Show the messagebox
                dlg.Destroy() #Destroy the messagebox when finished)
                self.chGrid.Disable()

    def OnOutputDirButton(self,event):
        sys.stdout = self.logger
        sys.stderr = self.logger
        """Open a file"""
        self.OutputDir = ''
        dlg = wx.DirDialog(self, "Choose output location")
        if dlg.ShowModal() == wx.ID_OK:
            self.OutputDir = dlg.GetPath()
            self.OutputPath.SetValue(self.OutputDir)
        dlg.Destroy()

    def OnGenerate(self,event):
        sys.stdout = self.logger
        sys.stderr = self.logger
        print("Checking the inputs.....")
        print()
        # Checking one-by-one manually
        ChekupMarkerflag = {}

        if self.MainData is None:
            msgs = 'MainData not loaded.'
            ChekupMarkerflag['MainData'] = (False,msgs,self.MainData)
        else:
            msgs = 'MainData loaded!'
            ChekupMarkerflag['MainData'] = (True,msgs,self.MainData)

        if self.selectedVarList is None:
            msgs ='Variables not yet selected.'
            ChekupMarkerflag['selectedVarList'] = (False,msgs,self.selectedVarList)
        else:
            msgs = 'Variables selected.'
            ChekupMarkerflag['selectedVarList'] = (True,msgs,self.selectedVarList)

        if len(self.path_to_variables) == 0:
            msgs = 'Variables path not supplied. \n So, it will redirect to single site generation!'
            #This one is still set as True as it will redirect to single site generation
            ChekupMarkerflag['path_to_variables'] = (True,msgs,self.path_to_variables)
        else:
            msgs = 'Variables path selected. \n So, it will redirect to multisite generation!'
            ChekupMarkerflag['path_to_variables'] = (True,msgs,self.path_to_variables)

        if len(self.variable_files) == 0:
            msgs = 'Variable files not supplied!'
            #This one is still set as True as it will redirect to single site generation
            ChekupMarkerflag['variable_files'] = (False,msgs,self.variable_files)
        else:
            msgs = 'Variables files supplied!'
            ChekupMarkerflag['variable_files'] = (True,msgs,self.variable_files)

        if len(self.changes_params) == 0:
            msgs = 'Changes parameter not defined!'
            ChekupMarkerflag['changes_params'] = (False,msgs,self.changes_params)
        else:
            msgs = 'Changes parameter defined!'
            ChekupMarkerflag['changes_params'] = (True,msgs,self.changes_params)

        if self.precipitation_column is None:
            msgs = 'precipitation_column not defined!'
            ChekupMarkerflag['precipitation_column'] = (False,msgs,self.precipitation_column)
        else:
            msgs = 'precipitation_column defined!'
            ChekupMarkerflag['precipitation_column'] = (True,msgs,self.precipitation_column)

        for keys,values in ChekupMarkerflag.items():
            if values[0] is False:
                print(values[1])
                print()
            else:
                print(values[1])
                print(values[2])
                print()

        if self.OutputDir is None:
            msgs = 'Output directory is not yet set. So, setting it to current working directory!'
            self.OutputDir = os.getcwd();
            print(msgs)

        self.wet_threshold = self.WetThresholdBox.GetValue()
        print("Wet threshold set to {}".format(self.wet_threshold))

        Flags = []
        for keys,values in ChekupMarkerflag.items():
            Flags.append(values[0])

        store_results = {}  # Will store based on the number of simulations
                            # starting from 1
        print('Starting...!')
        if np.array(Flags).all() == True:
            # Make folder to store the result
            outdir = os.path.join(self.OutputDir,'OUTPUT_CC')
            if not os.path.exists(outdir):
                os.mkdir(outdir)
            #apply_gamma_map_multisite(variable_dictionary, precip_keyname_in_var_dict,\
                              #wet_threshold, mapped_columnname,desired_changes)

            #apply_deltashift_multisite(variable_dictionary, variable_keyname_in_var_dict,\
                               #mapped_columnname,desired_shifts):
            for key,value in self.variable_files.items():
                if key == self.precipitation_column:
                    R = wg.apply_gamma_map_multisite(self.variable_files, \
                                                  self.precipitation_column,\
                                                  self.wet_threshold, \
                                                  mapped_columnname = 'CC',\
                                                  desired_changes = self.changes_params[key])
                else:
                    ch1 = self.changes_params[key]
                    #print(self.variable_files)
                    #print(key)
                    #print(ch1[0].copy())
                    R = wg.apply_deltashift_multisite(self.variable_files, \
                                                  key,\
                                                  mapped_columnname = 'CC',\
                                                  desired_shifts = ch1[0].copy())
                fname1 = 'CC_' + key +".csv"
                fpathname1 = os.path.join(outdir,fname1)
                R.to_csv(fpathname1)
                store_results[key] = R
        else:
            textmsg = """Please check missing or errorneous inputs!"""
            dlg = wx.MessageDialog(self,textmsg,"Reminder",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)
        print()
        print('Ended!')


    def OnResetAll(self,event):
        # These are variables for k-NN simulation
        self.MainData = None
        self.selectedVarList = None
        self.path_to_variables = []
        self.precipitation_column = None
        self.variable_files = {} #Default
        self.changes_params = {}
        self.wet_threshold = 0.1
        self.OutputDir = None
        self.changes_files_to_save = None

        self.MainDataPath.SetValue('')
        self.combo_precip_declare.SetSelection(-1)
        self.WetThresholdBox.SetValue(0.1)
        self.OutputPath.SetValue('')
        self.chGrid.ClearGrid()
        ncols = self.chGrid.GetNumberCols()
        self.chGrid.DeleteCols(pos = 0 , numCols= ncols)
        self.chGrid.AppendCols(numCols = 10)
        for j in range(0,10):
            self.chGrid.SetColLabelValue(j,str(j))
        self.chGrid.Disable()

        self.logger.SetValue('')

    def OnClearLogger(self,event):
        self.logger.SetValue("")
#%%
###-----------------------------------###-----------------------------------###
class AnnualSeriesSimulator(wx.Panel):
    """k-NN and ARMA based anuual series simulator"""
    def __init__(self, parent):
        self.MainSeries = None
        self.nlagslim = 1
        self.arma_mod = None
        self.durbin_watson_stat = None
        self.normaltest_stat = None
        self.resid = None
        self.simulated_data = None
        self.simulatedARMAseries = None
        self.resid_nlags = None
        self.OutputDir = None

        wx.Panel.__init__(self, parent,style = wx.BORDER_SUNKEN)

        # create some sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=0, vgap=0)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)

        p = 0
        #Create an button to load main data
        self.loadseriesButton = wx.Button(self,label = "Load series ")
        # Add to the sizer grid
        grid.Add(self.loadseriesButton , pos = (p, 0), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.loadseriesButton.Bind(wx.EVT_BUTTON,self.OnLoadSeries)

        #Create an static text box calles text0
        self.MainSeriesPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.MainSeriesPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)

        self.plotseries = wx.Button(self,label = "Plot series ")
        # Add to the sizer grid
        grid.Add(self.plotseries , pos = (p, 2), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.plotseries.Bind(wx.EVT_BUTTON,self.OnPlotSeries)

        p += 1

        self.nlagsstatic = wx.StaticText(self, label = "Enter lags")
        grid.Add(self.nlagsstatic, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating box for setting moving window size
        self.nlags = wx.lib.intctrl.IntCtrl(self,value = 5, \
                              style = wx.TE_PROCESS_ENTER, min = 1,\
                              max = None, \
                              limited = 1)
        grid.Add(self.nlags, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)

        #Create an button to plot acf and pacf
        self.plot_acf = wx.Button(self,label = "Plot acf and pacf ")
        # Add to the sizer grid
        grid.Add(self.plot_acf  , pos = (p, 2), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.plot_acf.Bind(wx.EVT_BUTTON,self.OnPlotAcf)


        p += 1
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        #Create an static text box
        self.text200 = wx.StaticText(self,label = "ARMA PARAMETERS")
        self.text200.SetFont(font)
        self.text200.SetForegroundColour((0,0,255))
        grid.Add(self.text200, pos = (p, 0),span = (1,2), flag = wx.ALL, border = 5)

        p += 1
        #
        self.arma_p_static = wx.StaticText(self, label = "p")
        grid.Add(self.arma_p_static, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating box for setting moving window size
        self.arma_p = wx.lib.intctrl.IntCtrl(self,value = 1, \
                              style = wx.TE_PROCESS_ENTER, min = 1,\
                              max = None, \
                              limited = 1)
        grid.Add(self.arma_p, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)

        p += 1
        self.arma_q_static = wx.StaticText(self, label = "q")
        grid.Add(self.arma_q_static, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating box for setting moving window size
        self.arma_q = wx.lib.intctrl.IntCtrl(self,value = 1, \
                              style = wx.TE_PROCESS_ENTER, min = 1,\
                              max = None, \
                              limited = 1)
        grid.Add(self.arma_q, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)

        #Create an button to plot acf and pacf
        self.arma_fit = wx.Button(self,label = "Fit ARMA model ")
        # Add to the sizer grid
        grid.Add(self.arma_fit, pos = (p, 2), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.arma_fit.Bind(wx.EVT_BUTTON,self.OnArmaFit)

        p += 1
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        #Create an static text box
        self.text300 = wx.StaticText(self,label = "RESIDUAL ANALYSIS")
        self.text300.SetFont(font)
        self.text300.SetForegroundColour((0,0,255))
        grid.Add(self.text300, pos = (p, 0),span = (1,2), flag = wx.ALL, border = 5)

        p += 1
        #Create an button to plot acf and pacf
        self.plot_residuals = wx.Button(self,label = "Plot residuals ")
        # Add to the sizer grid
        grid.Add(self.plot_residuals, pos = (p, 0), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.plot_residuals.Bind(wx.EVT_BUTTON,self.OnPlotResiduals)

        #Create an button to plot acf and pacf
        self.view_residuals = wx.Button(self,label = "View summary")
        # Add to the sizer grid
        grid.Add(self.view_residuals, pos = (p, 1), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.view_residuals.Bind(wx.EVT_BUTTON,self.OnViewResiduals)

        p += 1
        # Check for autocorrelation in the residuals
        self.check_durbin_watson = wx.Button(self,label = "Test autocorrelation")
        # Add to the sizer grid
        grid.Add(self.check_durbin_watson, pos = (p, 0),flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.check_durbin_watson.Bind(wx.EVT_BUTTON,self.OnCheckDurbinWatson)

        #Check for the normality in the residuals
        self.check_normality = wx.Button(self,label = "Test normality")
        # Add to the sizer grid
        grid.Add(self.check_normality, pos = (p, 1), span = (1,2),flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.check_normality.Bind(wx.EVT_BUTTON,self.OnCheckNormal)

        p += 1
        self.residnlagsstatic = wx.StaticText(self, label = "Enter lags")
        grid.Add(self.residnlagsstatic, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating box for setting moving window size
        self.resid_nlags = wx.lib.intctrl.IntCtrl(self,value = 5, \
                              style = wx.TE_PROCESS_ENTER, min = 1,\
                              max = None, \
                              limited = 1)
        grid.Add(self.resid_nlags, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)

        #Create an button to plot acf and pacf
        self.resid_plot_acf = wx.Button(self,label = "Plot resid acf/pacf ")
        # Add to the sizer grid
        grid.Add(self.resid_plot_acf  , pos = (p, 2), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.resid_plot_acf.Bind(wx.EVT_BUTTON,self.OnPlotResidAcf)

        p += 1
        #Check for the normality in the residuals
        self.check_resid_acf = wx.Button(self,label = "Test acf for n lags")
        # Add to the sizer grid
        grid.Add(self.check_resid_acf , pos = (p, 0), span = (1,2),flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.check_resid_acf.Bind(wx.EVT_BUTTON,self.OnCheckResidAcf)

        p += 1
        self.text400 = wx.StaticText(self,label = "SIMULATION")
        self.text400.SetFont(font)
        self.text400.SetForegroundColour((0,0,255))
        grid.Add(self.text400, pos = (p, 0),span = (1,2), flag = wx.ALL, border = 5)

        p += 1

        lblList = ['Same as input', 'Enter below']
        self.rbox = wx.RadioBox(self, label = 'Simulation period', choices = lblList, \
                                majorDimension = 1, style = wx.RA_SPECIFY_ROWS)
        grid.Add(self.rbox, pos = (p, 0),span = (1,2), flag = wx.ALL, border = 5)
        self.rbox.Bind(wx.EVT_RADIOBOX,self.OnRadioBox)

        p += 1

        self.text500 = wx.StaticText(self,label = "Length of simulation")
        grid.Add(self.text500, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating box for setting moving window size
        self.nsim = wx.lib.intctrl.IntCtrl(self,value = 20, \
                              style = wx.TE_PROCESS_ENTER, min = 1,\
                              max = 100, \
                              limited = 1)
        grid.Add(self.nsim, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)

        p += 1

        self.text501 = wx.StaticText(self,label = "Enter year")
        grid.Add(self.text501, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating box for setting moving window size
        self.srtyear = wx.lib.intctrl.IntCtrl(self,value = 2000, \
                              style = wx.TE_PROCESS_ENTER, min = 1,\
                              max = 2999, \
                              limited = 1)
        grid.Add(self.srtyear, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.nsim.Disable()
        self.srtyear.Disable()

        p += 1
        #Check for the normality in the residuals
        self.simulate_arma = wx.Button(self,label = "Simulate ARMA")
        self.simulate_arma.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, \
                                            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.simulate_arma.SetForegroundColour(wx.Colour(0, 100, 0))
        grid.Add(self.simulate_arma , pos = (p, 0), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.simulate_arma.Bind(wx.EVT_BUTTON,self.OnSimulateARMA)

        self.plotresults = wx.Button(self,label = "Plot results ")
        # Add to the sizer grid
        grid.Add(self.plotresults , pos = (p, 1), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.plotresults.Bind(wx.EVT_BUTTON,self.OnPlotResults)

        self.ResetButton = wx.Button(self,label = "Reset All ")
        # Add to the sizer grid
        grid.Add(self.ResetButton , pos = (p, 2), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.ResetButton.Bind(wx.EVT_BUTTON,self.OnReset)

        p += 1
        #Create an button to load folder option to save
        self.OutputDirButton = wx.Button(self,label = "Output location ")
        grid.Add(self.OutputDirButton, pos = (p, 0), flag = wx.ALL, border = 5)
        self.OutputDirButton.Bind(wx.EVT_BUTTON,self.OnOutputDirButton)

        self.OutputPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        grid.Add(self.OutputPath, pos = (p,1), flag = wx.ALL, border = 5)

        #Create an button to save the data
        self.SaveButton = wx.Button(self,label = "Save results ")
        grid.Add(self.SaveButton, pos = (p, 2), flag = wx.ALL, border = 5)
        self.SaveButton.Bind(wx.EVT_BUTTON,self.OnSave)

        vSizer2 = wx.BoxSizer(wx.VERTICAL)
        # Creating the frame to plot the graph
        # plt.rcParams.update({'font.size': 8})
        self.figure = plt.figure(figsize=(2.0, 1.50),layout='constrained')
        #self.figure , (self.axes1,self.axes2, self.axes3) = plt.subplots(nrows = 3,figsize=(7.0, 5.0))
        self.axes1 = self.figure.add_subplot(311)
        self.axes2 = self.figure.add_subplot(312)
        self.axes3 = self.figure.add_subplot(313)
        self.axes1.grid(True,'major',color = (0.95,0.95,0.95))
        self.axes2.grid(True,'major',color = (0.95,0.95,0.95))
        self.axes3.grid(True,'major',color = (0.95,0.95,0.95))
        #self.figure.set_tight_layout({'pad': 5})
        self.canvas = FigureCanvas(self,-1,self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.SetSize((1,1))
        self.toolbar.Realize()
        self.canvas.draw()

        #self.toolbar.Hide()
        vSizer2.Add(self.toolbar,0, flag = wx.ALL|wx.EXPAND,border = 5 )
        vSizer2.Add(self.canvas,0,flag = wx.ALL|wx.EXPAND, border =5)
        vSizer2.AddSpacer(2)
        self.ClearPlot = wx.Button(self,label = 'Clear Plots')
        vSizer2.Add(self.ClearPlot,0,wx.ALL|wx.ALIGN_RIGHT, border = 5)
        self.ClearPlot.Bind(wx.EVT_BUTTON,self.OnClearPlot)

        self.logger2 = wx.TextCtrl(self, size = (100,150), style = wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH)
        self.logger2.SetInsertionPointEnd()
        self.logger2_ds = self.logger2.GetDefaultStyle()
        # Logger to display outputs or processing outputs
        vSizer2.Add(self.logger2,1,flag = wx.ALL|wx.EXPAND, border = 5)
        #Add clear button to clear the logger text
        self.ClearLoggerButton = wx.Button(self,label = "Clear Logger")
        vSizer2.Add(self.ClearLoggerButton,0,wx.ALL|wx.ALIGN_RIGHT,border = 5)
        self.ClearLoggerButton.Bind(wx.EVT_BUTTON,self.OnClearLogger)

        self.toolbar.update()
        hSizer.Add(grid, 1, flag = wx.ALL|wx.EXPAND, border = 5)
        hSizer.Add(vSizer2,1,flag = wx.ALL|wx.EXPAND, border = 5)
        mainSizer.Add(hSizer, 0, wx.ALL, 5)
        self.SetSizerAndFit(mainSizer)
        self.Layout()
        self.Fit()

    def OnClearPlot(self,event):
        self.axes1.clear()
        self.axes1.grid(True,'major',color = (0.95,0.95,0.95))
        self.axes2.clear()
        self.axes2.grid(True,'major',color = (0.95,0.95,0.95))
        self.axes3.clear()
        self.axes3.grid(True,'major',color = (0.95,0.95,0.95))
        self.canvas.draw()

    def OnLoadSeries(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        """Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose series data file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            self.MainSeriesPath.SetValue(f)
            # display this in file control
            MainSeries = pd.read_csv(f,header = 0,parse_dates=True)
            MainSeries.index = pd.to_datetime(MainSeries.Date,format="%Y-%m-%d")
            MainSeries.drop(columns = ['Date'],inplace  = True)
            MainSeries = MainSeries.asfreq('AS')
            cols=[i for i in MainSeries.columns if i not in ["Date","date","year","month","day"]]
            for col in cols:
                MainSeries[col]=pd.to_numeric(MainSeries[col],errors='coerce')
            # self.control.SetValue(f.read()) #This is showing data on the logger
            self.MainSeries = MainSeries
            print("Data loaded and convert into pandas dataframe!")
            print("Its columns are: {}".format(self.MainSeries.columns))
            # Plot the series in the top graph
            print(self.MainSeries)
            # print datatypes
            print("Datatype:")
            print(self.MainSeries.dtypes)
            self.nlagslim = len(self.MainSeries)- 1
            self.nlags.SetBounds(min=1, max=self.nlagslim)
            self.resid_nlags.SetBounds(min=1, max=self.nlagslim)
            self.axes1.clear()
            self.axes1.grid(True,'major',color = (0.95,0.95,0.95))
            for col in cols:
                self.axes1.plot(self.MainSeries.index, self.MainSeries[col],label = col)
            self.axes1.legend()
            self.canvas.draw()
        dlg.Destroy()

    def OnPlotSeries(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            self.axes1.clear()
            self.axes1.grid(True,'major',color = (0.95,0.95,0.95))
            for col in self.MainSeries.columns:
                self.axes1.plot(self.MainSeries.index, self.MainSeries[col],label = col)
            self.axes1.legend()
            self.canvas.draw()
        except:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            print("Load the data first! or Check the data! \n")
            self.logger2.SetDefaultStyle(self.logger2_ds)

    def OnPlotAcf(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            self.axes2.clear()
            self.axes3.clear()
            self.axes2.grid(True,'major',color = (0.95,0.95,0.95))
            self.axes3.grid(True,'major',color = (0.95,0.95,0.95))
            dta = self.MainSeries
            #print(dta)
            nlags = self.nlags.GetValue()
            #print(dta.values.squeeze())
            sm.graphics.tsa.plot_acf(dta.values.squeeze(), lags=nlags, ax=self.axes2)
            acf_df = pd.DataFrame(columns = ['acf'])
            acf_vals = sm.tsa.acf(dta.values.squeeze(), nlags = nlags)
            acf_df['acf'] = acf_vals
            acf_df.index.name = 'lags'
            print(acf_df)
            sm.graphics.tsa.plot_pacf(dta.values, lags = nlags, ax=self.axes3)
            pacf_df = pd.DataFrame(columns = ['pacf'])
            pacf_vals = sm.tsa.pacf(dta.values.squeeze(), nlags=nlags)
            pacf_df['pacf'] = pacf_vals
            pacf_df.index.name = 'lags'
            print(pacf_df)
            self.axes2.set_ylim([-1.1, 1.1])
            self.axes3.set_ylim([-1.1, 1.1])
            self.canvas.draw()
        except Exception as e:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            text0 = """Check:
                        1.Load the data first!
                        2.Check the data!
                        3. >> """
            text1 = str(e)
            print(text0 + text1)
            self.logger2.SetDefaultStyle(self.logger2_ds)

    def OnPlotResidAcf(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            self.axes2.clear()
            self.axes3.clear()
            self.axes2.grid(True,'major',color = (0.95,0.95,0.95))
            self.axes3.grid(True,'major',color = (0.95,0.95,0.95))
            dta = self.arma_mod.resid
            #print(dta)
            resid_nlags = self.resid_nlags.GetValue()
            #print(dta.values.squeeze())
            sm.graphics.tsa.plot_acf(dta.values.squeeze(), lags=resid_nlags, ax=self.axes2)
            sm.graphics.tsa.plot_pacf(dta.values, lags=resid_nlags, ax=self.axes3)
            self.axes2.set_ylim([-1.1, 1.1])
            self.axes3.set_ylim([-1.1, 1.1])
            self.canvas.draw()
        except:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            print("Obtain residuals first! or Check the data! \n")
            self.logger2.SetDefaultStyle(self.logger2_ds)

    def OnArmaFit(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            self.param_p = self.arma_p.GetValue()
            self.param_q = self.arma_q.GetValue()
            print("p: {}".format(self.param_p))
            print("q: {}".format(self.param_q))
            print(self.MainSeries.values)
            self.arma_mod = statsmodels.tsa.arima.model.ARIMA(self.MainSeries, \
                                        (self.param_p,self.param_q)).fit(disp=False)
            self.resid = self.arma_mod.resid
            print(self.arma_mod.params)
            print(self.arma_mod.summary())
        except Exception as e:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            text1 = str(e)
            text0 = """ ARMA model fit error. Try:
                1.Load the data if not loaded
                2.Check the data. Fill missing data if exists.
                3.>> """
            print(text0 + text1)
            self.logger2.SetDefaultStyle(self.logger2_ds)

    def OnPlotResiduals(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            self.axes1.clear()
            self.axes1.grid(True,'major',color = (0.95,0.95,0.95))
            self.axes1.plot(self.resid.index, self.resid.values,label = 'residuals')
            self.axes1.legend()
            self.canvas.draw()
        except:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            print("Please get\ check the residuals first!")
            self.logger2.SetDefaultStyle(self.logger2_ds)

    def OnViewResiduals(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            print('Residuals: ')
            print(self.resid)
            print ('Residuals Summary: ')
            print(self.resid.describe())
        except:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            print("Please get\ check the residuals first!")
            self.logger2.SetDefaultStyle(self.logger2_ds)

    def OnCheckDurbinWatson(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            self.durbin_watson_stat = sm.stats.durbin_watson(self.arma_mod.resid.values)
            text = """
            The Durbin-Watson statistic will always have a value between 0 and 4.
            A value of 2.0 means that there is no autocorrelation detected in the sample.
            Values from 0 to less than 2 indicate positive autocorrelation.
            Values from from 2 to 4 indicate negative autocorrelation.
            """
            print(text)
            print("Durbin Watson statistic = {}".format(self.durbin_watson_stat))
        except:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            print("Please try fit the model first! or something is wrong! Please Check")
            self.logger2.SetDefaultStyle(self.logger2_ds)

    def OnCheckNormal(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            self.normaltest_stat = stats.normaltest(self.arma_mod.resid)
            text = """
            D’Agostino and Pearson’s test for normality.
            Test whether a sample differs from a normal distribution.
            Null hypothesis that a sample comes from a normal distribution.
            If p < alpha: Null hypothesis can be rejected.
            If p >= alpha: Null hypothesis cannot be rejected.
            """
            print(text)
            print("K² statistic = {}".format(self.normaltest_stat[0]))
            print("p value = {}".format(self.normaltest_stat[1]))
        except:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            print("Please try fit the model first! or something is wrong! Please Check")
            self.logger2.SetDefaultStyle(self.logger2_ds)

    def OnCheckResidAcf(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            text = """
            This is checking if the residuals shows autocorrelation for different
            lags.
            AC - Autocorrelation
            Q - Ljung-Box Q-Statistic
            Prob - p-values associated with the Q-statistics
            """
            print(text)
            r,q,p = sm.tsa.acf(self.resid.values.squeeze(), qstat=True)
            n = self.resid_nlags.GetValue() + 1
            data = np.c_[range(1,n), r[1:n], q[1:n], p[1:n]]
            table = pd.DataFrame(data, columns=['lag', "AC", "Q", "Prob(>Q)"])
            print(table.set_index('lag'))
        except:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            print("Obtain \ Check for residuals or nlags! Something wrong!")
            self.logger2.SetDefaultStyle(self.logger2_ds)
        pass

    def OnSimulateARMA(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            const = self.arma_mod.params[0]
            arparams = self.arma_mod.arparams
            maparams = self.arma_mod.maparams
            arparams = np.r_[1, -arparams] #This is creating arma process
            maparams = np.r_[1, maparams]
            arma_model_process = ArmaProcess(arparams, maparams)
            std_noise = self.resid.std()
            l = self.rbox.GetStringSelection()
            if l == 'Same as input':
                ns = len(self.MainSeries)
                res_df = pd.DataFrame(index = self.MainSeries.index, columns = ['precip'])
                res_df.index.name = 'Date'
            elif l == 'Enter below':
                ns = self.nsim.GetValue()
                srtyear = self.srtyear.GetValue()
                srtdate = datetime(srtyear,1,1)
                dateseries = pd.date_range(start =srtdate, periods = ns, freq = "Y")
                res_df = pd.DataFrame(index = dateseries, columns = ['precip'])
                res_df.index.name = 'Date'
            print('Standard deviation of the residuals: {}'.format(std_noise))
            print('Checking: Is ARMA invertible?')
            print('Answer: {}'.format(arma_model_process.isinvertible))
            print('Checking: Is ARMA stationary?')
            print('Answer: {}'.format(arma_model_process.isstationary))
            print('Simulation....!')
            # ARMA simulation of random variable of ARMA process
            arma_rvs = arma_model_process.generate_sample(nsample=1000, burnin=1000-ns,\
                                                          scale = std_noise)
            arma_rvs = arma_rvs + const
            self.simulated_data = np.round(arma_rvs[-ns:],2)
            print(self.simulated_data)
            res_df['precip'] = self.simulated_data.copy()
            self.simulatedARMAseries = res_df.copy()
            print(self.simulatedARMAseries)
        except:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            text = """Something wrong! Please check the followings:
                1. Fit the model
                2. Check the residuals
                3. Check input data
                """
            print(text)
            self.logger2.SetDefaultStyle(self.logger2_ds)

    def OnRadioBox(self,event):
        l = self.rbox.GetStringSelection()
        if l == 'Same as input':
            self.nsim.SetValue(20)
            self.nsim.Disable()
            self.srtyear.SetValue(2000)
            self.srtyear.Disable()
        elif l == 'Enter below':
            self.nsim.Enable()
            self.srtyear.Enable()

    def OnPlotResults(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            self.axes1.grid(True,'major',color = (0.95,0.95,0.95))
            for col in self.simulatedARMAseries.columns:
                self.axes1.plot(self.simulatedARMAseries.index, self.simulatedARMAseries[col],label = 'sim ' + col)
            self.axes1.legend()
            self.canvas.draw()
        except:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            text = """Something wrong! Please recheck simulation / simulated data"""
            print(text)
            self.logger2.SetDefaultStyle(self.logger2_ds)

    def OnOutputDirButton(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        """Open a file"""
        self.OutputDir = ''
        dlg = wx.DirDialog(self, "Choose output location")
        if dlg.ShowModal() == wx.ID_OK:
            self.OutputDir = dlg.GetPath()
            self.OutputPath.SetValue(self.OutputDir)
        dlg.Destroy()

    def OnSave(self,event):
        sys.stdout = self.logger2
        sys.stderr = self.logger2
        try:
            if self.OutputDir is None:
                msgs = 'Output directory is not yet set. So, setting it to current working directory!'
                self.OutputDir = os.getcwd();
                print(msgs)
            fname1 = 'ARMA_annual_series.csv'
            fpathname1 = os.path.join(self.OutputDir,fname1)
            self.simulatedARMAseries.to_csv(fpathname1)
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.GREEN))
            print("File saved as {}.".format(fpathname1))
            self.logger2.SetDefaultStyle(self.logger2_ds)
        except:
            self.logger2.SetDefaultStyle(wx.TextAttr(wx.RED))
            text = """Something wrong! Nothing to save! Please Check! """
            print(text)
            self.logger2.SetDefaultStyle(self.logger2_ds)

    def OnReset(self,event):
        self.MainSeries = None
        self.nlagslim = 1
        self.arma_mod = None
        self.durbin_watson_stat = None
        self.normaltest_stat = None
        self.resid = None
        self.simulated_data = None
        self.simulatedARMAseries = None
        self.OutputDir = None

        # Setting the text ctrls values
        self.MainSeriesPath.SetValue('')
        self.nlags.SetValue(5)
        self.arma_p.SetValue(1)
        self.arma_q.SetValue(1)
        self.resid_nlags.SetValue(5)
        self.nsim.SetValue(20)
        self.srtyear.SetValue(2000)
        self.OutputPath.SetValue('')

        # Clearing the plots
        self.axes1.clear()
        self.axes1.grid(True,'major',color = (0.95,0.95,0.95))
        self.axes2.clear()
        self.axes2.grid(True,'major',color = (0.95,0.95,0.95))
        self.axes3.clear()
        self.axes3.grid(True,'major',color = (0.95,0.95,0.95))
        self.canvas.draw()
        # Clear the logger
        self.logger2.SetValue("")

    def OnClearLogger(self,event):
        self.logger2.SetValue("")
#%%
class WGCRA(wx.Panel):
    """Simulates the weather based on k-NN algorithm conditioned on the
    annual series.
    """
    def __init__(self,parent):
        wx.Panel.__init__(self, parent,style = wx.BORDER_SUNKEN)

        self.ObsAnnualPrecipSeries = None
        self.SimAnnualPrecipSeries = None
        self.MainData = None
        self.selectedVarList = None
        self.path_to_variables = []
        self.precipitation_column = None
        self.no_simulations = 1 #Default
        self.variable_files = {} #Default
        self.nStates = 3 #Default
        self.wet_threshold = 0.1
        self.extreme_threshold = 0.8
        self.windowsize = 15
        self.weights_method = None
        self.weights = None
        self.initial_pstate = None
        self.initialWV = None
        self.OutputDir = None
        self.CheckStatus = 0
        self.FinalResults = None
        self.originalTP = None
        self.changes_in_TP = None

        # create some sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=0, vgap=0)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)

        # grid position counter, Now working in level 0
        p = 0

        #Create an static text box calles text0
        self.text0 = wx.StaticText(self,label = "INPUTS")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text0.SetFont(font)
        self.text0.SetForegroundColour((0,0,255)) # set text color
        # Add to the sizer grid
        grid.Add(self.text0, pos = (p, 0), flag = wx.ALL, border = 5)

        p += 1
        #Create an button to load observed annual series
        self.LoadObsAnnual = wx.Button(self,label = "Load Obs Annual Data")
        # Add to the sizer grid
        grid.Add(self.LoadObsAnnual, pos = (p, 0), flag = wx.ALL, border = 5)
        self.LoadObsAnnual.Bind(wx.EVT_BUTTON,self.OnLoadObsAnnual)

        #Create an static text box to load the path of load observed annual series
        self.ObsAnnualPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.ObsAnnualPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)


        p += 1
        #Create an button to load observed annual series
        self.LoadSimAnnual = wx.Button(self,label = "Load Sim Annual Data")
        # Add to the sizer grid
        grid.Add(self.LoadSimAnnual, pos = (p, 0), flag = wx.ALL, border = 5)
        self.LoadSimAnnual.Bind(wx.EVT_BUTTON,self.OnLoadSimAnnual)

        #Create an static text box to load the path of load observed annual series
        self.SimAnnualPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.SimAnnualPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)

        p += 1

        #Create an button to load main data
        self.B0 = wx.Button(self,label = "Load Main Data ")
        # Add to the sizer grid
        grid.Add(self.B0, pos = (p, 0), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.B0.Bind(wx.EVT_BUTTON,self.LoadMainData)

        #Create an static text box calles text0
        self.MainDataPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.MainDataPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)

        #Create an button to select varaibles
        self.SelectVarsButton = wx.Button(self,label = 'Select Variables')
        grid.Add(self.SelectVarsButton, pos = (p,2), flag = wx.ALL, border = 5)
        self.SelectVarsButton.Bind(wx.EVT_BUTTON,self.SelectVars)

        p += 1

        # Create an static text box named text for declaring precipitation column
        self.textprecip = wx.StaticText(self, label = "Select Precipitation column")
        grid.Add(self.textprecip, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating choices
        choices1 = [] #This is the states for number of states
        self.combo_precip_declare = wx.ComboBox(self,id=wx.ID_ANY,choices = choices1, \
                                                    style = wx.LB_SINGLE)
        grid.Add(self.combo_precip_declare, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo_precip_declare.Bind(wx.EVT_COMBOBOX, self.Oncombo_precip_declare)

        #Create an button to set path to multisite variables files
        self.PathVarsFileButton = wx.Button(self,label = 'Load Variable Files')
        grid.Add(self.PathVarsFileButton, pos = (p,2), flag = wx.ALL, border = 5)
        self.PathVarsFileButton.Bind(wx.EVT_BUTTON,self.PathandLoadVarsFile)

        p += 1

        #Create an static text box calles text0
        self.text55 = wx.StaticText(self,label = "MODEL PARAMETERS")
        self.text55.SetFont(font)
        self.text55.SetForegroundColour((0,0,255))
        grid.Add(self.text55, pos = (p, 0), flag = wx.ALL, border = 5)

        p += 1

        # Create an static text box named text for number of states
        self.text88 = wx.StaticText(self, label = "Number of resamples")
        grid.Add(self.text88, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating box for setting moving window size
        self.nresamplesBox = wx.lib.intctrl.IntCtrl(self,value = 20, \
                              style = wx.TE_PROCESS_ENTER, min = 1, max = 100, \
                              limited = 1)
        grid.Add(self.nresamplesBox, pos = (p, 1), flag = wx.ALL, border = 5)
        self.nresamplesBox.Bind(wx.EVT_TEXT_ENTER,self.OnNresamples)
        self.nresamplesBox.Bind(wx.EVT_TEXT,self.OnNresamples)


        # Create an static text box named text for number of states
        self.text1 = wx.StaticText(self, label = "Number of states")
        grid.Add(self.text1, pos = (p, 2), flag = wx.ALL, border = 5)

        # Creating number of states list box
        self.state_list = ['2','3'] #This is the states for number of states
        self.combo1 = wx.ComboBox(self,id=wx.ID_ANY,value = "3",choices = self.state_list, style = wx.LB_SINGLE)
        grid.Add(self.combo1, pos = (p, 3), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo1.Bind(wx.EVT_COMBOBOX, self.OnCombo)

        p += 1

        # Create an static text box named text for number of states
        self.sbox_wet = wx.StaticText(self, label= "Wet Threshold")
        grid.Add(self.sbox_wet, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creading the wet threshold box
        self.WetThresholdBox = wx.lib.masked.numctrl.NumCtrl(self,value = 0.1, \
                               style = wx.TE_PROCESS_ENTER, \
                               integerWidth = 3, fractionWidth=2, \
                               min = 0.0, max = 100.0, limited = 1,\
                               allowNegative=False, allowNone = True)
        grid.Add(self.WetThresholdBox, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.WetThresholdBox.Bind(wx.EVT_TEXT_ENTER,self.OnWetThresholdBox)
        self.WetThresholdBox.Bind(wx.EVT_TEXT,self.OnWetThresholdBox)

        # Create an static text box named text for number of states
        self.sbox_extreme = wx.StaticText(self, label= "Extreme Threshold")
        grid.Add(self.sbox_extreme, pos = (p, 2), flag = wx.ALL, border = 5)

        # Creading the wet threshold box
        self.ExtremeThresholdBox = wx.lib.masked.numctrl.NumCtrl(self,value = 0.8, \
                               style = wx.TE_PROCESS_ENTER, \
                               integerWidth = 1, fractionWidth=2, \
                               min = 0.0, max = 1.0, limited = 1,\
                               allowNegative=False, allowNone = True)
        grid.Add(self.ExtremeThresholdBox, pos = (p, 3), flag = wx.ALL|wx.EXPAND, border = 5)
        self.ExtremeThresholdBox.Bind(wx.EVT_TEXT_ENTER,self.OnExtremeThresholdBox)
        self.ExtremeThresholdBox.Bind(wx.EVT_TEXT,self.OnExtremeThresholdBox)

        p += 1

        # Create an static text box named text for number of states
        self.sbox_window = wx.StaticText(self, label= "Moving Window Size")
        grid.Add(self.sbox_window, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating box for setting moving window size
        self.Mov_win_Box = wx.lib.intctrl.IntCtrl(self,value = 15, \
                              style = wx.TE_PROCESS_ENTER, min = 7, max = 61, \
                              limited = 0)
        grid.Add(self.Mov_win_Box, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.Mov_win_Box.Bind(wx.EVT_TEXT_ENTER,self.OnMov_win_Box)
        self.Mov_win_Box.Bind(wx.EVT_TEXT,self.OnMov_win_Box)

        # Create an static text box for display selecting weights method
        self.sbox_weights = wx.StaticText(self, label= "Assign weights by ")
        grid.Add(self.sbox_weights, pos = (p, 2), flag = wx.ALL, border = 5)

        # Creating number of states list box
        self.weights_method_list = ["equal","user_defined","inv_std"] #This is the states for number of states
        self.WeightsCombo = wx.ComboBox(self,id=wx.ID_ANY, \
                                        choices = self.weights_method_list, \
                                        style = wx.LB_SINGLE)
        grid.Add(self.WeightsCombo, pos = (p, 3), flag = wx.ALL|wx.EXPAND, border = 5)
        self.WeightsCombo.Bind(wx.EVT_COMBOBOX, self.OnWeightsCombo)
        #print(self.weights)

        p += 1

        #Create an static text box calles text0
        self.text2a = wx.StaticText(self,label = "Transition probability")
        # Add to the sizer grid
        grid.Add(self.text2a, pos = (p, 0), flag = wx.ALL, border = 5)

        self.TP_view = wx.Button(self, label = "View")
        grid.Add(self.TP_view, pos = (p, 1), flag = wx.ALL, border = 5)
        self.TP_view.Bind(wx.EVT_BUTTON,self.OnTPview)

        self.TP_change = wx.Button(self, label = "Change")
        grid.Add(self.TP_change, pos = (p, 2), flag = wx.ALL, border = 5)
        self.TP_change.Bind(wx.EVT_BUTTON,self.OnTPchange)

        p += 1

        #Create an static text box calles text0
        self.text2 = wx.StaticText(self,label = "INITIAL CONDITIONS")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text2.SetFont(font)
        self.text2.SetForegroundColour((0,0,255)) # set text color
        # Add to the sizer grid
        grid.Add(self.text2, pos = (p, 0), flag = wx.ALL, border = 5)

        p += 1
        # Create an static text box named text for number of states
        self.text3 = wx.StaticText(self, label = "Precipitation State")
        grid.Add(self.text3, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creating number of states list box
        self.istate_list = ['0','1','2']
        self.combo2 = wx.ComboBox(self,id=wx.ID_ANY,value = "",choices = self.istate_list, style = wx.LB_SINGLE)
        grid.Add(self.combo2, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo2.Bind(wx.EVT_COMBOBOX, self.OnCombo2)

        self.WVButton = wx.Button(self, label = "Weather variables")
        grid.Add(self.WVButton, pos = (p, 2), flag = wx.ALL, border = 5)
        self.WVButton.Bind(wx.EVT_BUTTON,self.OnWVButton)

        p += 1
        #Create an static text box
        self.text4 = wx.StaticText(self,label = "SIMULATION")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text4.SetFont(font)
        self.text4.SetForegroundColour((0,0,255)) # set text color
        # Add to the sizer grid
        grid.Add(self.text4, pos = (p, 0), flag = wx.ALL, border = 5)

        p += 1
        self.text5 = wx.StaticText(self, label = "Note: Simulation period will be same as that of simulated annual series.")
        grid.Add(self.text5, pos = (p, 0),span = (1,3), flag = wx.ALL, border = 5)

        p += 1
        #Create an button for output location
        self.OutputDirButton = wx.Button(self,label = "Output location ")
        # Add to the sizer grid
        grid.Add(self.OutputDirButton, pos = (p, 0), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.OutputDirButton.Bind(wx.EVT_BUTTON,self.OnOutputDirButton)

        #Create an static text box calles text0
        self.OutputPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.OutputPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)

        p += 1
        self.CheckInputs = wx.Button(self,label = "Check inputs")
        # Add to the sizer grid
        grid.Add(self.CheckInputs, pos = (p, 0), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.CheckInputs.Bind(wx.EVT_BUTTON,self.OnCheckInputs)

        self.ResetAll = wx.Button(self,label = "Reset All")
        # Add to the sizer grid
        grid.Add(self.ResetAll, pos = (p, 1), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.ResetAll.Bind(wx.EVT_BUTTON,self.OnResetAll)


        p += 1

        self.SimulateButton = wx.Button(self,label = 'Simulate')
        self.SimulateButton.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, \
                                            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.SimulateButton.SetForegroundColour(wx.Colour(0, 100, 0))
        grid.Add(self.SimulateButton, pos = (p,0), span = (1,2), flag = wx.EXPAND|wx.ALL, border = 5)
        self.SimulateButton.Bind(wx.EVT_BUTTON, self.OnSimulate)

        self.WriteResults = wx.Button(self,label = 'Write results')
        grid.Add(self.WriteResults, pos = (p,2), flag = wx.ALL, border = 5)
        self.WriteResults.Bind(wx.EVT_BUTTON, self.OnWriteResults)

        # Logger to display outputs or processing outputs
        vSizer2 = wx.BoxSizer(wx.VERTICAL)

        self.logger3 = wx.TextCtrl(self,size = (200,-1), style = wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH)
        self.logger3.SetInsertionPointEnd()
        self.logger3_ds = self.logger3.GetDefaultStyle()
        #redirect text here
        #redir1=RedirectText(self.logger1)
        #sys.stdout = redir1
        #sys.stderr = redir1
        vSizer2.Add(self.logger3,1,flag = wx.ALL|wx.EXPAND, border = 5)

        #Add clear button to clear the logger text
        self.ClearLoggerButton = wx.Button(self,label = "Clear Logger")
        vSizer2.Add(self.ClearLoggerButton,0,wx.ALL|wx.ALIGN_RIGHT,border = 5)
        self.ClearLoggerButton.Bind(wx.EVT_BUTTON,self.OnClearLogger)

        hSizer.Add(grid, 1, flag = wx.ALL|wx.EXPAND, border = 5)
        hSizer.Add(vSizer2,1,flag = wx.ALL|wx.EXPAND, border = 5)
        mainSizer.Add(hSizer, 0, wx.ALL, 5)
        self.SetSizerAndFit(mainSizer)
        self.Fit()

    def OnLoadObsAnnual(self,event):
        """Open a file"""
        self.dirname = ''
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        dlg = wx.FileDialog(self, "Choose observed annual precipitation data file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            self.ObsAnnualPath.SetValue(f)
            # display this in file control
            ObsAnnual = pd.read_csv(f,header = 0,parse_dates=True)
            ObsAnnual.index.rename('id',inplace=True)
            ObsAnnual.Date = pd.to_datetime(ObsAnnual.Date, format="%Y-%m-%d")
            cols=[i for i in ObsAnnual.columns if i not in ["Date","date","year","month","day"]]
            for col in cols:
                ObsAnnual[col]=pd.to_numeric(ObsAnnual[col],errors='coerce')
            self.ObsAnnualPrecipSeries = ObsAnnual
            print("Data loaded and convert into pandas dataframe!")
            print("Its columns are: {}".format(self.ObsAnnualPrecipSeries.columns))
            print("Data: \n")
            self.logger3.SetDefaultStyle(wx.TextAttr(wx.Colour(0,145,0)))
            print(self.ObsAnnualPrecipSeries)
            self.logger3.SetDefaultStyle(self.logger3_ds)
        dlg.Destroy()

    def OnLoadSimAnnual(self,event):
        """Open a file"""
        self.dirname = ''
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        dlg = wx.FileDialog(self, "Choose simulated annual precipitation data file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            self.SimAnnualPath.SetValue(f)
            # display this in file control
            SimAnnual = pd.read_csv(f,header = 0,parse_dates=True)
            SimAnnual.index.rename('id',inplace=True)
            SimAnnual.Date = pd.to_datetime(SimAnnual.Date, format="%Y-%m-%d")
            cols=[i for i in SimAnnual.columns if i not in ["Date","date","year","month","day"]]
            for col in cols:
                SimAnnual[col]=pd.to_numeric(SimAnnual[col],errors='coerce')
            self.SimAnnualPrecipSeries = SimAnnual
            print("Data loaded and convert into pandas dataframe!")
            print("Its columns are: {}".format(self.SimAnnualPrecipSeries.columns))
            print("Data: \n")
            self.logger3.SetDefaultStyle(wx.TextAttr(wx.Colour(0,145,0)))
            print(self.SimAnnualPrecipSeries)
            self.logger3.SetDefaultStyle(self.logger3_ds)
        dlg.Destroy()

    def LoadMainData(self,event):
        """Open a file"""
        self.dirname = ''
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        dlg = wx.FileDialog(self, "Choose main data file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            self.MainDataPath.SetValue(f)
            # display this in file control
            MainData = pd.read_csv(f,header = 0,parse_dates=True)
            MainData.index.rename('id',inplace=True)
            MainData.Date = pd.to_datetime(MainData.Date, format="%Y-%m-%d")
            cols=[i for i in MainData.columns if i not in ["Date","date","year","month","day"]]
            for col in cols:
                MainData[col]=pd.to_numeric(MainData[col],errors='coerce')
            # self.control.SetValue(f.read()) #This is showing data on the logger
            self.MainData = MainData
            print("Data loaded and convert into pandas dataframe!")
            print("Its columns are: {}".format(self.MainData.columns))
            print("Data: \n")
            self.logger3.SetDefaultStyle(wx.TextAttr(wx.Colour(0,145,0)))
            print(self.MainData)
            self.logger3.SetDefaultStyle(self.logger3_ds)
        dlg.Destroy()

    def SelectVars(self,event):
        """Select the variables"""
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        if self.MainData is None:
            textmsg = """Please load the main data first!"""
            dlg = wx.MessageDialog(self,textmsg,"Variable selection ",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)
        else:
            vlist = list(self.MainData.columns)
            y = VarSelectionFrame(self,title="Select the variables",var_list = vlist)
            y.ShowModal()
            self.selectedVarList = y.selectedVarList
            print("Selected variables are: {}".format(self.selectedVarList))

            # Laoding the varibales into combo box for declaration
            self.combo_precip_declare.Clear()
            for i in self.selectedVarList:
                self.combo_precip_declare.Append(i)

    def PathandLoadVarsFile(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        if self.selectedVarList is None:
            textmsg = """Please select the variables first!"""
            dlg = wx.MessageDialog(self,textmsg,"Set path to files",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)
        else:
            y1 = SetPathVariableFilesFrame(self,title = 'Set path to weather variable files', \
                                        sel_var_list = self.selectedVarList)
            y1.ShowModal()
            self.path_to_variables = y1.sel_var_path
            print("Path of variable files are: ")
            print(self.path_to_variables) #This is dictionary
            # Loading the data
            for keys,values in self.path_to_variables.items():
                varfile = pd.read_csv(values,header = 0,parse_dates=True)
                varfile.index.rename('id',inplace=True)
                varfile.Date = pd.to_datetime(varfile.Date,format="%Y-%m-%d")
                cols=[i for i in varfile.columns if i not in ["Date","date","year","month","day"]]
                for col in cols:
                    varfile[col]=pd.to_numeric(varfile[col],errors='coerce')
                print("File {} loaded as {}!".format(values,keys))
                self.variable_files[keys] = varfile

    def Oncombo_precip_declare(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        id1 = self.combo_precip_declare.GetSelection()
        self.precipitation_column = self.selectedVarList[id1]
        print("precipitation_column is {}.".format(self.precipitation_column))

    def OnNresamples(self,event):
        self.nresamples = int(self.nresamplesBox.GetLineText(0))

    def OnCombo(self, event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        nStatesId = self.combo1.GetSelection()
        self.nStates = int(self.state_list[nStatesId])
        if self.nStates == 2:
            self.ExtremeThresholdBox.Disable()
            self.combo2.Clear()
            self.combo2.Append('0')
            self.combo2.Append('1')
        elif self.nStates == 3:
            self.ExtremeThresholdBox.Enable()
            self.combo2.Clear()
            self.combo2.Append('0')
            self.combo2.Append('1')
            self.combo2.Append('2')

    def OnWetThresholdBox(self,event):
        n = float(self.WetThresholdBox.GetLineText(0))
        self.wet_threshold = n
        #print("Wet Threshold set to: {}".format(self.wet_threshold))

    def OnExtremeThresholdBox(self,event):
        n = float(self.ExtremeThresholdBox.GetLineText(0))
        self.extreme_threshold = n
        #print("Extreme Threshold set to: {}".format(self.extreme_threshold))

    def OnMov_win_Box(self,event):
        n = float(self.Mov_win_Box.GetLineText(0))
        self.windowsize = n

    def OnWeightsCombo(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        Id = self.WeightsCombo.GetSelection()
        self.weights_method = self.weights_method_list[Id]
        print("Weighing method given to weigh the variables in k-NN is '{}'.".format(self.weights_method))
        if self.weights_method == self.weights_method_list[1]:
            if self.selectedVarList is not None:
                y3 = WeightsFrame(self,title = 'Provide weights', \
                                            sel_var_list = self.selectedVarList,\
                                            precip_var_name = self.precipitation_column,\
                                            nature = 'weights')
                y3.ShowModal()
                self.weights = y3.sel_var_weights
                print("'user_defined' weights set to {}".format(self.weights))
            else:
                textmsg = """Please select the variables first!"""
                dlg = wx.MessageDialog(self,textmsg,"Reminder!",wx.OK)
                dlg.ShowModal() #Show the messagebox
                dlg.Destroy() #Destroy the messagebox when finished)

    def OnTPview(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        print("Checking the inputs.....")
        print()
        # Checking one-by-one manually
        ChekupMarkerflag = {}

        if self.MainData is None:
            msgs = 'MainData not loaded.'
            ChekupMarkerflag['MainData'] = (False,msgs,self.MainData)
        else:
            msgs = 'MainData loaded!'
            ChekupMarkerflag['MainData'] = (True,msgs,self.MainData)

        if self.selectedVarList is None:
            msgs ='Variables not yet selected.'
            ChekupMarkerflag['selectedVarList'] = (False,msgs,self.selectedVarList)
        else:
            msgs = 'Variables selected.'
            ChekupMarkerflag['selectedVarList'] = (True,msgs,self.selectedVarList)

        if self.precipitation_column is None:
            msgs = 'precipitation_column not defined!'
            ChekupMarkerflag['precipitation_column'] = (False,msgs,self.precipitation_column)
        else:
            msgs = 'precipitation_column defined!'
            ChekupMarkerflag['precipitation_column'] = (True,msgs,self.precipitation_column)

        for keys,values in ChekupMarkerflag.items():
            if values[0] is False:
                print(values[1])
                print()
            else:
                print(values[1])
                print(values[2])
                print()

        nStatesId = self.combo1.GetSelection()
        self.nStates = int(self.state_list[nStatesId])
        print("Number of precipitation states set to {}".format(self.nStates))

        self.wet_threshold = self.WetThresholdBox.GetValue()
        print("Wet threshold set to {}".format(self.wet_threshold))

        self.extreme_threshold = self.ExtremeThresholdBox.GetValue()
        print("Extreme threshold set to {}".format(self.extreme_threshold))

        Flags = []
        for keys,values in ChekupMarkerflag.items():
            Flags.append(values[0])

        if np.array(Flags).all() == True:
            aWG1 = wg.WeatherDTS(self.MainData, name = 'computeTP', \
                                precipitation_column_name = self.precipitation_column, \
                                var_dict = {})
            # Setting up the model parameters
            aWG1.setNoStates(nostates = self.nStates)
            aWG1.setWetThreshold(wet_threshold_value = self.wet_threshold)
            aWG1.setExtremeThreshold(extreme_threshold_value = self.extreme_threshold)
            self.originalTP = aWG1.getTP().round(3)
            #self.originalTP.to_csv('TP.csv')
            tp_frame1 = TP_Frame_View(self,title ='Transition probability', \
                                 TP =self.originalTP, \
                                 nstates = self.nStates)
            tp_frame1.ShowModal()
            print('Transition Probability Viewed!')
        else:
            print("Cannot compute TP!. Please check the inputs first!")

    def OnTPchange(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        try:
            aWG1 = wg.WeatherDTS(self.MainData, name = 'computeTP', \
                                precipitation_column_name = self.precipitation_column, \
                                var_dict = {})
            # Setting up the model parameters
            aWG1.setNoStates(nostates = self.nStates)
            aWG1.setWetThreshold(wet_threshold_value = self.wet_threshold)
            aWG1.setExtremeThreshold(extreme_threshold_value = self.extreme_threshold)
            self.originalTP = aWG1.getTP().round(3)
            tp_frame2 = TP_Frame_Change(self,title ='Transition probability', \
                                 TP =self.originalTP, \
                                 nstates = self.nStates)
            tp_frame2.ShowModal()
            self.changes_in_TP = tp_frame2.newTPch
            #self.newTP = self.originalTP + self.changes_in_TP
            print("Changes in transition probability:")
            print("")
            print(self.changes_in_TP)
        except Exception as e:
            msg = "Cannot compute TP!. Please check the inputs first! \n"
            print(msg + str(e) )

    def OnCombo2(self, event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        nStatesId = self.combo2.GetSelection()
        self.initial_pstate = int(self.istate_list[nStatesId])
        print("Initial precipitation state is {}.".format(self.initial_pstate))

    def OnWVButton(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        if self.selectedVarList is not None:
            y4 = WeightsFrame(self,title = 'Provide values', \
                                        sel_var_list = self.selectedVarList, \
                                        precip_var_name = self.precipitation_column,\
                                        nature = 'values')
            y4.ShowModal()
            self.initialWV = y4.sel_var_weights
            print("Intial values of weather variables set to {}".format(self.initialWV))
        else:
            textmsg = """Please select the variables first!"""
            dlg = wx.MessageDialog(self,textmsg,"Reminder!",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy() #Destroy the messagebox when finished)

    def OnOutputDirButton(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        """Open a file"""
        self.OutputDir = ''
        dlg = wx.DirDialog(self, "Choose output location")
        if dlg.ShowModal() == wx.ID_OK:
            self.OutputDir = dlg.GetPath()
            self.OutputPath.SetValue(self.OutputDir)
        dlg.Destroy()

    def OnCheckInputs(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        print("Checking the inputs.....")
        print()
        # Checking one-by-one manually
        ChekupMarkerflag = {}
        if (self.ObsAnnualPrecipSeries is None) :
            msgs = 'Observed annual precipitation series is not loaded.'
            ChekupMarkerflag['ObsAnnualPrecipSeries'] = (False,msgs,self.ObsAnnualPrecipSeries)
        elif (self.ObsAnnualPrecipSeries.empty == True):
            msgs = 'Observed annual precipitation series is empty.'
            ChekupMarkerflag['ObsAnnualPrecipSeries'] = (False,msgs,self.ObsAnnualPrecipSeries)
        else:
            msgs = 'Observed annual precipitation is loaded!'
            ChekupMarkerflag['ObsAnnualPrecipSeries'] = (True,msgs,self.ObsAnnualPrecipSeries)

        if (self.SimAnnualPrecipSeries is None) :
            msgs = 'Simulated annual precipitation series is not loaded.'
            ChekupMarkerflag['SimAnnualPrecipSeries'] = (False,msgs,self.SimAnnualPrecipSeries)
        elif (self.SimAnnualPrecipSeries.empty == True):
            msgs = 'Simulated annual precipitation series is empty.'
            ChekupMarkerflag['SimAnnualPrecipSeries'] = (False,msgs,self.SimAnnualPrecipSeries)
        else:
            msgs = 'Simulated annual precipitation is loaded!'
            ChekupMarkerflag['SimAnnualPrecipSeries'] = (True,msgs,self.SimAnnualPrecipSeries)

        if self.MainData is None:
            msgs = 'MainData not loaded.'
            ChekupMarkerflag['MainData'] = (False,msgs,self.MainData)
        else:
            msgs = 'MainData loaded!'
            ChekupMarkerflag['MainData'] = (True,msgs,self.MainData)

        if self.selectedVarList is None:
            msgs ='Variables not yet selected.'
            ChekupMarkerflag['selectedVarList'] = (False,msgs,self.selectedVarList)
        else:
            msgs = 'Variables selected.'
            ChekupMarkerflag['selectedVarList'] = (True,msgs,self.selectedVarList)

        if len(self.path_to_variables) == 0:
            msgs = 'Variables path not supplied. \n So, it will redirect to single site generation!'
            #This one is still set as True as it will redirect to single site generation
            ChekupMarkerflag['path_to_variables'] = (True,msgs,self.path_to_variables)
        else:
            msgs = 'Variables path selected. \n So, it will redirect to multisite generation!'
            ChekupMarkerflag['path_to_variables'] = (True,msgs,self.path_to_variables)

        if self.precipitation_column is None:
            msgs = 'precipitation_column not defined!'
            ChekupMarkerflag['precipitation_column'] = (False,msgs,self.precipitation_column)
        else:
            msgs = 'precipitation_column defined!'
            ChekupMarkerflag['precipitation_column'] = (True,msgs,self.precipitation_column)

        if len(self.variable_files) == 0:
            msgs = 'Variable files not supplied. \n So, it will redirect to single site generation!'
            #This one is still set as True as it will redirect to single site generation
            ChekupMarkerflag['variable_files'] = (True,msgs,self.variable_files)
        else:
            msgs = 'Variables files supplied. \n So, it will redirect to multisite generation!'
            ChekupMarkerflag['variable_files'] = (True,msgs,self.variable_files)

        if self.weights_method is None:
            msgs = 'Method for weights is not yet supplied!'
            ChekupMarkerflag['weights_method'] = (False,msgs,self.weights_method)
        else:
            msgs = 'Method for weights is supplied!'
            ChekupMarkerflag['weights_method'] = (True,msgs,self.weights_method)

        if self.weights_method == 'user_defined':
            if self.weights is None:
                msgs = 'Weights is not yet supplied!'
                ChekupMarkerflag['weights'] = (False,msgs,self.weights_method)
            else:
                msgs = 'Weights supplied!'
                ChekupMarkerflag['weights'] = (True,msgs,self.weights_method)

        if self.initial_pstate is None:
            msgs = 'Intial state for precipitation is not yet set!'
            ChekupMarkerflag['initial_pstate'] = (False,msgs,self.initial_pstate)
        else:
            msgs = 'Intial state for precipitation is set!'
            ChekupMarkerflag['initial_pstate'] = (True,msgs,self.initial_pstate)

        if self.initialWV is None:
            msgs = 'Intial weather vectors is not yet set!'
            ChekupMarkerflag['initialWV'] = (False,msgs,self.initialWV)
        else:
            msgs = 'Intial weather vectors is set!'
            ChekupMarkerflag['initialWV'] = (True,msgs,self.initialWV)
        pass

        for keys,values in ChekupMarkerflag.items():
            if values[0] is False:
                print(values[1])
                print()
            else:
                print(values[1])
                self.logger3.SetDefaultStyle(wx.TextAttr(wx.Colour(0,145,0)))
                print(values[2])
                self.logger3.SetDefaultStyle(self.logger3_ds)
                print()

        if self.OutputDir is None:
            msgs = 'Output directory is not yet set. So, setting it to current working directory!'
            self.OutputDir = os.getcwd();
            print(msgs)

        # Getting the values from the boxes
        self.nresamples = int(self.nresamplesBox.GetLineText(0))
        print("Number of annual precip resamples set to {}".format(self.nresamples))

        nStatesId = self.combo1.GetSelection()
        self.nStates = int(self.state_list[nStatesId])
        print("Number of precipitation states set to {}".format(self.nStates))

        self.wet_threshold = self.WetThresholdBox.GetValue()
        print("Wet threshold set to {}".format(self.wet_threshold))

        self.extreme_threshold = self.ExtremeThresholdBox.GetValue()
        print("Extreme threshold set to {}".format(self.extreme_threshold))

        if self.changes_in_TP is None:
            print("No user-defined changes in Transition Probability found! So, no changes will be made to original TP")
        else:
            print("User-defined changes in Transition Probability found and it will be used in simulation")
            print("User defined changes in TP:")
            print(self.changes_in_TP)

        self.windowsize = self.Mov_win_Box.GetValue()
        print("windowsize set to {}".format(self.windowsize))

        Flags = []
        for keys,values in ChekupMarkerflag.items():
            Flags.append(values[0])

        if np.array(Flags).all() == True:
            self.CheckStatus = 1
            self.logger3.SetDefaultStyle(wx.TextAttr(wx.GREEN))
            text = """Ready to simulate!"""
            print(text)
            self.logger3.SetDefaultStyle(self.logger3_ds)
        else:
            self.CheckStatus = 0
            self.logger3.SetDefaultStyle(wx.TextAttr(wx.RED))
            text = """Please check missing or errorneous inputs!"""
            print(text)
            self.logger3.SetDefaultStyle(self.logger3_ds)

    def OnSimulate(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        if self.CheckStatus == 0:
            self.logger3.SetDefaultStyle(wx.TextAttr(wx.RED))
            print('Please check the inputs first!')
            self.logger3.SetDefaultStyle(self.logger3_ds)
        else:
            # Preparing inputs
            multisite_dict = self.variable_files
            precipitation_column_name = self.precipitation_column

            # Preparing model parameters in the dictionary as inputs
            self.nresamples = int(self.nresamplesBox.GetLineText(0))
            nStatesId = self.combo1.GetSelection()
            self.nStates = int(self.state_list[nStatesId])
            self.wet_threshold = self.WetThresholdBox.GetValue()
            self.extreme_threshold = self.ExtremeThresholdBox.GetValue()
            self.windowsize = self.Mov_win_Box.GetValue()
            model_params_dict = {'nResamples': self.nresamples,
                     'nStates': self.nStates,
                     'wet_threshold': self.wet_threshold,
                     'extreme_threshold': self.extreme_threshold,
                     'changes_in_TP': self.changes_in_TP,
                     'window_size': self.windowsize,
                     'weights_type': self.weights_method,
                     'iState': self.initial_pstate,
                     'initialWV':self.initialWV,
                     'varlist': self.selectedVarList}
            if self.weights_method == 'user_defined':
                model_params_dict['weights'] = self.weights
            else:
                model_params_dict['weights'] = []

            self.logger3.SetDefaultStyle(wx.TextAttr(wx.Colour(0,145,0)))
            print('Starting simulation...')
            Results = wg.wg_cra(self.SimAnnualPrecipSeries,\
                               self.ObsAnnualPrecipSeries,\
                               self.MainData,\
                               precipitation_column_name,\
                               multisite_dict,\
                               model_params_dict)
            print('Simulation ended!')
            self.FinalResults = Results
            print(Results)
            self.logger3.SetDefaultStyle(self.logger3_ds)
            pass

    def OnWriteResults(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        if self.FinalResults is None:
            self.logger3.SetDefaultStyle(wx.TextAttr(wx.RED))
            print('Please carry simulation first!')
            self.logger3.SetDefaultStyle(self.logger3_ds)
        else:
            self.logger3.SetDefaultStyle(wx.TextAttr(wx.Colour(0,145,0)))
            outdir = os.path.join(self.OutputDir,'OUTPUT_WGCRA')
            if not os.path.exists(outdir):
                os.mkdir(outdir)
            print("File outputs will be created in: ")
            print(outdir)
            # For mainfile
            fname0 = 'WGCRA_simulation_maindata.csv';
            fpathname0 = os.path.join(outdir,fname0)
            self.FinalResults[0].to_csv(fpathname0, index = False)
            # For multisite file
            for var_name,var_data in self.FinalResults[1].items():
                fname1 = 'WGCRA_simulation_multisite_' + var_name +'.csv';
                fpathname1 = os.path.join(outdir,fname1)
                var_data.to_csv(fpathname1, index = False)
            print("Output files created!")
            self.logger3.SetDefaultStyle(self.logger3_ds)
            pass

    def OnResetAll(self,event):
        self.ObsAnnualPrecipSeries = None
        self.SimAnnualPrecipSeries = None
        self.MainData = None
        self.selectedVarList = None
        self.path_to_variables = []
        self.precipitation_column = None
        self.no_simulations = 1 #Default
        self.variable_files = {} #Default
        self.nStates = 3 #Default
        self.wet_threshold = 0.1
        self.extreme_threshold = 0.8
        self.windowsize = 15
        self.weights_method = None
        self.weights = None
        self.initial_pstate = None
        self.initialWV = None
        self.OutputDir = None
        self.CheckStatus = 0
        self.FinalResults = None
        self.originalTP = None
        self.changes_in_TP = None

        self.ObsAnnualPath.SetValue('')
        self.SimAnnualPath.SetValue('')
        self.MainDataPath.SetValue('')

        self.nresamplesBox.SetValue(20)
        self.combo1.SetSelection(1)
        self.combo2.SetSelection(-1)
        self.WeightsCombo.SetSelection(-1)
        self.combo_precip_declare.Clear()
        self.WetThresholdBox.SetValue(0.1)
        self.ExtremeThresholdBox.SetValue(0.8)
        self.Mov_win_Box.SetValue(15)
        self.OutputPath.SetValue('')

        self.logger3.SetValue("")

    def OnClearLogger(self,event):
        self.logger3.SetValue("")
#%%
#%%
class BCSD(wx.Panel):
    """Simulates the weather based on k-NN algorithm conditioned on the
    annual series.
    """
    def __init__(self,parent):
        wx.Panel.__init__(self, parent,style = wx.BORDER_SUNKEN)

        self.ObsHistoricalData = None
        self.ObsVarname = None
        self.ModelHindcastData = None
        self.ModelVarname = None
        self.ModelFutureData = None
        self.givenVarname = None
        self.RegridEngList = ['CDO','XE REGRIDDER'];
        self.SelectedRegridEng = None
        self.RegridEngMethod = ['NN','BIL','CON'];
        self.SelectedRegridMethod = None
        self.wet_threshold = 1.0
        self.QMmethodlist = ['multiplicative','additive'];
        self.QMwindowlist = ['monthly'];
        self.SelectedQMmethod = None;
        self.DScorr = None;
        self.OutputDir = None
        self.factors = None;
        self.result_BCSD = None;

        # create some sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(hgap=0, vgap=0)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)

        # No 0
        p = 0
        ## grid position counter, Now working in level 0
        ## No 0
        self.text0 = wx.StaticText(self,label = "BCSD")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text0.SetFont(font)
        self.text0.SetForegroundColour((0,0,255)) # set text color
        # Add to the sizer grid
        grid.Add(self.text0, pos = (p, 0), flag = wx.ALL, border = 5)

        p +=1
        # No 1
        #Create an static text box calles text0
        self.text0 = wx.StaticText(self,label = "INPUTS")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text0.SetFont(font)
        self.text0.SetForegroundColour((0,0,255)) # set text color
        # Add to the sizer grid
        grid.Add(self.text0, pos = (p, 0), flag = wx.ALL, border = 5)

        # No 2
        p += 1
        #Create an button to load observed annual series
        self.LoadObsHistorical = wx.Button(self,label = "Load Obs Data")
        # Add to the sizer grid
        grid.Add(self.LoadObsHistorical, pos = (p, 0), flag = wx.ALL, border = 5)
        self.LoadObsHistorical.Bind(wx.EVT_BUTTON,self.OnLoadObsHistorical)

        #Create an static text box to load the path of load observed annual series
        self.ObsHistoricalPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.ObsHistoricalPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)

        # Create an static text box named text for selecting variable for obs
        self.textprecip = wx.StaticText(self, label = "Select Variable")
        grid.Add(self.textprecip, pos = (p, 2), flag = wx.ALL, border = 5)

        # Creating choices select the variable from the combo box
        choices1 = []
        self.combo_obsvar_declare = wx.ComboBox(self,id=wx.ID_ANY,choices = choices1, \
                                                    style = wx.LB_SINGLE)
        grid.Add(self.combo_obsvar_declare, pos = (p, 3), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo_obsvar_declare.Bind(wx.EVT_COMBOBOX, self.Oncombo_obsvar_declare)

        # No 3
        p += 1
        #Create an button to load observed annual series
        self.LoadModelHindcastData = wx.Button(self,label = "Load Model Data-hindcast")
        # Add to the sizer grid
        grid.Add(self.LoadModelHindcastData, pos = (p, 0), flag = wx.ALL, border = 5)
        self.LoadModelHindcastData.Bind(wx.EVT_BUTTON,self.OnLoadModelHindcastData)

        #Create an static text box to load the path of load observed annual series
        self.ModelHindcastPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.ModelHindcastPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)

        # Create an static text box named text for selecting variable for obs
        self.textprecip = wx.StaticText(self, label = "Select Variable")
        grid.Add(self.textprecip, pos = (p, 2), flag = wx.ALL, border = 5)

        # Creating choices select the variable from the combo box
        choices1 = []
        self.combo_modelvar_declare = wx.ComboBox(self,id=wx.ID_ANY,choices = choices1, \
                                                    style = wx.LB_SINGLE)
        grid.Add(self.combo_modelvar_declare, pos = (p, 3), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo_modelvar_declare.Bind(wx.EVT_COMBOBOX, self.Oncombo_modelvar_declare)

        #No4
        p += 1
        #Create an button to load main data
        self.B0 = wx.Button(self,label = "Load Model Data-future ")
        # Add to the sizer grid
        grid.Add(self.B0, pos = (p, 0), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.B0.Bind(wx.EVT_BUTTON,self.OnLoadModelFutureData)

        #Create an static text box to load the path of load observed annual series
        self.ModelFuturePath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.ModelFuturePath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)

        p += 1
        # Create an static text box named text for number of states
        self.sbox_wet = wx.StaticText(self, label= "Select Rain Threshold")
        grid.Add(self.sbox_wet, pos = (p, 0), flag = wx.ALL, border = 5)

        # Creading the wet threshold box
        self.WetThresholdBox = wx.lib.masked.numctrl.NumCtrl(self,value = 1.0, \
                               style = wx.TE_PROCESS_ENTER, \
                               integerWidth = 3, fractionWidth=2, \
                               min = 0.0, max = 100.0, limited = 1,\
                               allowNegative=False, allowNone = True)
        grid.Add(self.WetThresholdBox, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.WetThresholdBox.Bind(wx.EVT_TEXT_ENTER,self.OnWetThresholdBox)
        self.WetThresholdBox.Bind(wx.EVT_TEXT,self.OnWetThresholdBox)

        p += 1
        self.textregrideng = wx.StaticText(self, label = "Select regrid engine")
        grid.Add(self.textregrideng, pos = (p, 0), flag = wx.ALL, border = 5)

        choicesA = self.RegridEngList;
        self.combo_regrideng_declare = wx.ComboBox(self,id=wx.ID_ANY,choices = choicesA, \
                                                    style = wx.LB_SINGLE)
        grid.Add(self.combo_regrideng_declare, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo_regrideng_declare.Bind(wx.EVT_COMBOBOX, self.Oncombo_regrideng_declare)

        p +=1
        self.textregrideng = wx.StaticText(self, label = "Select regrid method")
        grid.Add(self.textregrideng, pos = (p, 0), flag = wx.ALL, border = 5)

        choicesB = self.RegridEngMethod;
        self.combo_regridmethod_declare = wx.ComboBox(self,id=wx.ID_ANY,choices = choicesB, \
                                                    style = wx.LB_SINGLE)
        grid.Add(self.combo_regridmethod_declare, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo_regridmethod_declare.Bind(wx.EVT_COMBOBOX, self.Oncombo_regridmethod_declare)

        p +=1
        self.textQMmethod = wx.StaticText(self, label = "Compute method")
        grid.Add(self.textQMmethod, pos = (p, 0), flag = wx.ALL, border = 5)

        self.combo_QMmethod_declare = wx.ComboBox(self,id=wx.ID_ANY,choices = self.QMmethodlist, \
                                                    style = wx.LB_SINGLE)
        grid.Add(self.combo_QMmethod_declare, pos = (p, 1), flag = wx.ALL|wx.EXPAND, border = 5)
        self.combo_QMmethod_declare.Bind(wx.EVT_COMBOBOX, self.Oncombo_QMmethod_declare)

        p += 1
        # For Bias correction using Quantile Mapping
        self.text0 = wx.StaticText(self,label = "Bias correcton - QM")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text0.SetFont(font)
        self.text0.SetForegroundColour((0,0,255)) # set text color
        # Add to the sizer grid
        grid.Add(self.text0, pos = (p, 0), flag = wx.ALL, border = 5)

        p +=1
        #Create an button to load observed annual series
        self.regrid = wx.Button(self,label = "REGRID obs to model res")
        # Add to the sizer grid
        grid.Add(self.regrid, pos = (p, 0), flag = wx.ALL, border = 5)
        self.regrid.Bind(wx.EVT_BUTTON,self.OnRegrid)

        p += 1
        #Create an button to load main data
        self.OutputDirButton = wx.Button(self,label = "Output filename ")
        # Add to the sizer grid
        grid.Add(self.OutputDirButton, pos = (p, 0), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.OutputDirButton.Bind(wx.EVT_BUTTON,self.OnOutputDirButton)

        #Create an static text box calles text0
        self.OutputPath = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        grid.Add(self.OutputPath, pos = (p,1), flag = wx.EXPAND|wx.ALL, border = 5)

        #p += 1
        # Perform quantile mapping and create a new file
        #Create an button to load observed annual series
        self.PerformQM = wx.Button(self,label = "Perform BC")
        # Add to the sizer grid
        grid.Add(self.PerformQM, pos = (p, 2), flag = wx.ALL, border = 5)
        self.PerformQM.Bind(wx.EVT_BUTTON,self.OnPerformQM)

        p += 1
        # For Bias correction using Quantile Mapping
        self.text01 = wx.StaticText(self,label = "Spatial Disaggregation - SD")
        font = wx.Font(10,wx.DEFAULT,wx.NORMAL, wx.BOLD)
        self.text01.SetFont(font)
        self.text01.SetForegroundColour((0,0,255)) # set text color
        # Add to the sizer grid
        grid.Add(self.text01, pos = (p, 0), flag = wx.ALL, border = 5)

        p += 1
        # Process daily observation climatology
        #Create an button to load observed annual series
        self.obs_climatology = wx.Button(self,label = "Process obs climatology")
        # Add to the sizer grid
        grid.Add(self.obs_climatology, pos = (p, 0), flag = wx.ALL, border = 5)
        self.obs_climatology.Bind(wx.EVT_BUTTON,self.OnProcess_obs_climatology)

        p +=1
        #Create an button to load observed annual series
        self.regrid2 = wx.Button(self,label = "REGRID obs clim to model res")
        # Add to the sizer grid
        grid.Add(self.regrid2, pos = (p, 0), flag = wx.ALL, border = 5)
        self.regrid2.Bind(wx.EVT_BUTTON,self.OnRegrid2)

        p +=1
        # Create an button to compute the factors
        self.processFactors = wx.Button(self,label = "Process factors")
        # Add to the sizer grid
        grid.Add(self.processFactors, pos = (p, 0), flag = wx.ALL, border = 5)
        self.processFactors.Bind(wx.EVT_BUTTON,self.OnProcessFactors)

        #p +=1
        # Create an button to interpolate the factos at obs resolution
        self.processFactors2 = wx.Button(self,label = "Interp factors at obs res")
        # Add to the sizer grid
        grid.Add(self.processFactors2, pos = (p, 1), flag = wx.ALL, border = 5)
        self.processFactors2.Bind(wx.EVT_BUTTON,self.OnProcessFactors2)

        p +=1
        #Create an button to process and get the final BCSD values
        self.getBCSDdata = wx.Button(self,label = "Get BCSD data")
        # Add to the sizer grid
        grid.Add(self.getBCSDdata, pos = (p, 0), flag = wx.ALL, border = 5)
        self.getBCSDdata.Bind(wx.EVT_BUTTON,self.OnGetBCSDdata)

        #Create an button to save final BCSD values
        self.saveBCSDdata = wx.Button(self,label = "Save results")
        # Add to the sizer grid
        grid.Add(self.saveBCSDdata, pos = (p, 1), flag = wx.ALL, border = 5)
        self.saveBCSDdata.Bind(wx.EVT_BUTTON,self.OnSaveBCSDdata)

        #p +=1
        self.ResetAll1 = wx.Button(self,label = "Reset All")
        # Add to the sizer grid
        grid.Add(self.ResetAll1, pos = (p, 2), flag = wx.ALL, border = 5)
        # Add the binder to LoadMainData
        self.ResetAll1.Bind(wx.EVT_BUTTON,self.OnResetAll1)

        # Logger to display outputs or processing outputs
        vSizer2 = wx.BoxSizer(wx.VERTICAL)
        self.logger3 = wx.TextCtrl(self,size = (200,-1), style = wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH)
        self.logger3.SetInsertionPointEnd()
        self.logger3_ds = self.logger3.GetDefaultStyle()
        #redirect text here
        #redir1=RedirectText(self.logger1)
        #sys.stdout = redir1
        #sys.stderr = redir1
        vSizer2.Add(self.logger3,1,flag = wx.ALL|wx.EXPAND, border = 5)

        #Add clear button to clear the logger text
        self.ClearLoggerButton = wx.Button(self,label = "Clear Logger")
        vSizer2.Add(self.ClearLoggerButton,0,wx.ALL|wx.ALIGN_RIGHT,border = 5)
        self.ClearLoggerButton.Bind(wx.EVT_BUTTON,self.OnClearLogger)

        hSizer.Add(grid, 1, flag = wx.ALL|wx.EXPAND, border = 5)
        hSizer.Add(vSizer2,1,flag = wx.ALL|wx.EXPAND, border = 5)
        mainSizer.Add(hSizer, 0, wx.ALL, 5)
        self.SetSizerAndFit(mainSizer)
        self.Fit()

    def sanitize_climdata(self,climdata,given_varname,varname,threshold=0.10):
        """
        convert to data array with only one variable with varname
        only the data greater than threshold are retained and other set to zero
        applies only for for precipitation dataset
        default precipitation threshold is 0.25 mm/day
        Parameters
        ----------
        climdata : xarray readable dataset or dataarray
            DESCRIPTION.
        given_varname : string
            Name of the variable as defined in the climdata
        varname : string
            variable type pr or tas or tasmax or any other
            Note: the given_varname will be converted into varname.
        threshold : float
            Threshold precipitation in mm/day.
            Only applicable for precipitation.
            All the precipitation values less than the threshold are set to zero.
            The default is 0.25.

        Returns
        -------
        climdata : xarray dataarray
            Cleaned dataarray of the variable.

        """
        # This will select only the required variable
        # and automatically will be defined as dataarray
        if isinstance(climdata,xr.core.dataarray.Dataset):
            climdata = climdata[given_varname].copy();

        # convert given given_varn7ame to varname
        climdata = climdata.rename(varname)

        if varname.lower() in ['pr','precip','p','prcp','tp','precipitation']:
            climdata = climdata.where(
                (climdata > threshold) | np.isnan(climdata),
                other=0);

        return climdata

    def Regridding(self,sanitized_fromdata,sanitized_todata,regrid_method):
        """ prefroms regrdding from obs to model resolution"""
        obs = sanitized_fromdata;
        model = sanitized_todata;

        # get the grid_descriptions
        gcmres=xr.Dataset(model.coords);
        obsres=xr.Dataset(obs.coords);

        regrid_engine=self.SelectedRegridEng;
        #regrid_method=self.SelectedRegridMethod;

        if regrid_engine == 'CDO':
            # create temp folder in the working directory if it doesn't exits
            temp_dir=os.path.join(os.getcwd(),'temp_cdo_folder');
            if not os.path.exists(temp_dir):
                # Create a new directory because it does not exist
                os.makedirs(temp_dir)

            cdo=CDO.Cdo(tempdir=temp_dir) ## create cdo object
            cdo.env = {'REMAP_EXTRAPOLATE': 'on'}
            grid_info_model=cdo.griddes(input=model.to_dataset())
            with open(os.path.join(temp_dir,'gridinfo.txt'), 'w') as f:
                for line in grid_info_model:
                    f.write(f"{line}\n");
            if regrid_method == 'NN':
                obs_at_modelres = cdo.remapnn(os.path.join(temp_dir,'gridinfo.txt'),
                                                  input=obs.to_dataset(),
                                                  returnXArray=self.ModelVarname);
            if regrid_method == 'BIL':
                obs_at_modelres = cdo.remapbil(os.path.join(temp_dir,'gridinfo.txt'),
                                                  input=obs.to_dataset(),
                                                  returnXArray=self.ModelVarname);
            if regrid_method == 'CON':
                obs_at_modelres = cdo.remapcon(os.path.join(temp_dir,'gridinfo.txt'),
                                                  input=obs.to_dataset(),
                                                  returnXArray=self.ModelVarname);
            #  clean cdo temporary files
            cdo.cleanTempDir()
            os.remove(os.path.join(temp_dir,'gridinfo.txt'))
        else:
            if regrid_method == 'NN':
                regrid_method_name = 'nearest_s2d';
            if regrid_method == 'BIL':
                regrid_method_name = 'bilinear';
            if regrid_method == 'CON':
                regrid_method_name = 'conservative';

            regridder = xe.Regridder(obsres,gcmres,regrid_method_name)
            obs_at_modelres = regridder(obs);

        obs_at_modelres = obs_at_modelres.rename(self.ModelVarname)
        obs_at_modelres = obs_at_modelres.assign_coords(lon=model.lon);
        obs_at_modelres = obs_at_modelres.assign_coords(lat=model.lat);
        result = obs_at_modelres;
        return result

    #% Quantile mapping function
    def qm(self, obs_data,hind_data,fut_data,opt1,opt2):
        """Quantile mapping function qm
        Requirements:
            Requires importing the followings:
            import numpy as np
            from statsmodels.distributions.empirical_distribution import ECDF
        Inputs:
            obs_data = numpy array of observed value (at reference period)
            hind_data = numpy array of hindcast value (gcm/ rcm at reference period)
            fut_data = numpy array of future value (or values to be corrected)
        Outputs:
            quantile mapped series
        opt1:
            "generic" -> this option is to use the np.quantile for inv.cdf with 'linear' interpolaation
            "aurtherlike" -> this option divided whole prabalities table into 100 parts
        opt2:
            "multiplicative" -> multiplicative scaling for precipitation
            "additive" -> additive factor for temperature

        Steps:
        # step1: Quantile mapping for fut_data,x, when minimum_value_in_hind <= x <= maximum_value_in_hind
        # step2: Scaling when fut_data,x, is outside limit of values in hind_data
        # step3: Frequency adapation
        References:

        Example:
        Example1 -
        obs = [0,0,0,0,0.5,1,1,1.2,2.5,2.6,2.6,2.65,3,3.1,3.1,4,4,4.5,4.5,4.5]
        hind = [0,0,0,0,0,0,0,0,0,0,1.2,1.3,2.5,3,3]
        fut = [0,0,0,0,1,2,1.5,3.5,2.1,0.5,6]
        qmapped_series = qm(obs,hind,fut,"aurtherlike","multiplicative")
        print(qmapped_series)
        >>>
        [0.         2.39397459 0.         0.         3.1        4.
         4.         5.25       4.         3.07797619 9.        ]
        Created by Dibesh Shrestha 2020
        """
        obs = obs_data.copy()
        hind = hind_data.copy()
        fut = fut_data.copy()
        qm_series = fut_data.copy() # This is to store the answer

        # ecdf for obs and hind-gcm series
        # Extracting ECDF function using statsmodels.distributions.empirical_distribution.ECDF
        ecdf_obs_fn = ECDF(obs)
        ecdf_hind_fn = ECDF(hind)
        # Probability in obs series for last 0 = ecdf_obs_fn(0)
        prob_0mm_obs = ecdf_obs_fn(0)
        # Probability in hind series for last 0 = ecdf_hind_fn(0)
        prob_0mm_hind = ecdf_hind_fn(0)
        # maximum and minimum of the obs series
        max_in_obs_series = np.quantile(obs,1,method = 'higher')
        min_in_obs_series = np.quantile(obs,0,method = 'lower')
        # maximum and minimum of the hind series
        max_in_hind_series = np.quantile(hind,1,method = 'higher')
        min_in_hind_series = np.quantile(hind,0,method = 'lower')

        #position or index that requires quantile mappping
        pos_requiring_qm = np.where((fut >= min_in_hind_series) & (fut <= max_in_hind_series))
        series_requiring_qm = fut[pos_requiring_qm]
        # position or index that requires scaling at upper limit
        pos_requiring_scaling_upper = np.where(fut > max_in_hind_series)
        # position or index that requires scaling at lower limit
        pos_requiring_scaling_lower = np.where(fut < min_in_hind_series)

        # No .1 Quanitle mapping
        # later it will corrected upper limits, lower limits and frequency adaptation
        # in steps 2 and 3
        if opt1 == "generic":
            # local quantile mapping
            cor_fut1 = np.quantile(obs,ecdf_hind_fn(series_requiring_qm),method='linear')
            pass
        if opt1 == "aurtherlike":
            probs = np.arange(0,1.01,0.01)
            obs_values_at_probs = np.quantile(obs,probs)
            hind_values_at_probs = np.quantile(hind,probs)
            def prob_a_in_x(x,a):
                # find the proability of a in x, like ecdf function
                # x is the 'hind_values_at_probs', x is numpy array
                # a is the raw value to be corrected, a is scalar
                # pos is position
                #print(a)
                try:
                    pos = np.where(x > a)[0][0]
                    x_max = x[pos]
                    x_min = x[pos-1]
                    # linear interpolation
                    prob = (pos-1)/100 + 0.01*(a-x_min)/(x_max-x_min)
                except:
                    prob = 1
                return prob
            # finding out the probabilities of future values in hind data
            # which is to say applaying ecdf function at hind
            positional_probs = np.array([prob_a_in_x(hind_values_at_probs,i) for i in series_requiring_qm])
            # converting that into the postional values
            index_max = np.int_(np.ceil(positional_probs*100)) #upper limit
            index_min = np.int_(np.floor(positional_probs*100)) #lower limit
            obs_max = obs_values_at_probs[index_max] #obs value at upper limit
            obs_min = obs_values_at_probs[index_min] #obs value at lower limit
            # applying linear inperpolation
            cor_fut1 = obs_min + (obs_max - obs_min)*(positional_probs*100-index_min)

        qm_series[pos_requiring_qm] = cor_fut1

        # No.2 Scaling (linear extrapolation)
        # two options additive and multiplicative
        if opt2 == "multiplicative":
            greater_values = fut[fut > max_in_hind_series]
            cor_greater_values = greater_values * max_in_obs_series/max_in_hind_series
            #print(greater_values)
            #print(max_in_obs_series,max_in_hind_series)
            #test_fut1[np.where(fut > max_in_hind_series)] = cor_greater_values

            lesser_values = fut[fut < min_in_hind_series]
            cor_lesser_values = lesser_values * min_in_obs_series/min_in_hind_series
            #test_fut2[np.where(fut < min_in_hind_series)] = cor_lesser_values
            pass
        if opt2 == "additive":
            # if opt2 is addtive
            greater_values = fut[fut > max_in_hind_series]
            cor_greater_values = greater_values + (max_in_obs_series - max_in_hind_series)
            #test_fut1[np.where(fut > max_in_hind_series)] = cor_greater_values

            lesser_values = fut[fut < min_in_hind_series]
            cor_lesser_values = lesser_values + (min_in_obs_series - min_in_hind_series)
            #test_fut2[np.where(fut < min_in_hind_series)] = cor_lesser_values
            pass
        qm_series[pos_requiring_scaling_upper] = cor_greater_values
        qm_series[pos_requiring_scaling_lower] = cor_lesser_values

        # No. 3 Frequency adaptation
        # Frequency adaptation
        # If prob_0mm_hind > prob_0mm_obs then we need frequency adapation for zero values
        # If prob_0mm_hind <= prob_0mm_obs then we don't need frequency adaption for zero values
        if prob_0mm_hind > prob_0mm_obs:
            # finding the extent for the frequency adaptation
            deltaP0 = (prob_0mm_hind-prob_0mm_obs)/prob_0mm_hind
            # Maximum value for the interpolation
            # value in obs series at position for last value of 0 in hind series if series are of
            # equal length else its value of obs series when inv_ecdf_obs(ecdf_hind(0))
            max_val_for_interp = np.quantile(obs,prob_0mm_hind,method='lower')
            # minimum value for interpolation is zero
            min_val_for_interp = 0
            # create a array an unifrom random array of shape fut
            randomvalues = np.random.uniform(0,1,fut.shape)

            # # FA is frequency adaptation
            # FA is to be done where the values are zero and random value < deltaP0
            #FA = (fut == 0) & (randomvalues < deltaP0)
            # position that requires frequency adaptation
            # first step
            pos_requiring_FA1 = np.where((fut == 0))
            qm_series[pos_requiring_FA1] = fut[pos_requiring_FA1]
            # second step
            pos_requiring_FA = np.where((fut == 0) & (randomvalues < deltaP0))
            #print(pos_requiring_FA)
            #print(fut[pos_requiring_FA])
            cor_FA = np.random.uniform(min_val_for_interp,max_val_for_interp,fut[pos_requiring_FA].shape)
            qm_series[pos_requiring_FA] = cor_FA
        return qm_series

    def qm_monthwise(self,DSobs,DShind,DSfut,var_name,correction_type):
        """ performs monthwise quantile mapping
        Inputs:
            DSobs = data file of observation in netcdf
            DShind = data file of hindcast data in netcdf
            DSfut = data file of future data in netcdf
            var_name = name of variable
            correction_type = 'multiplicative' or 'additive'
        Output:
            DScorr = data file of bias corrected data in netcdf
        """
        self.dirname = ''
        sys.stdout = self.logger3
        sys.stderr = self.logger3

        X = DSobs.copy();
        Y = DShind.copy();
        Z = DSfut.copy();

        lat_name_list = ['lat','latitude','y'];
        lon_name_list = ['lon','longitude','x'];
        #print(Z.dims);
        try:
            list_dimensions = [v.lower() for v in list(Z.dims.keys())];
        except:
            try:
                list_dimensions = [v.lower() for v in list(Z.dims)];
            except:
                raise AttributeError("Cannot access dimension names.")

        #check_lat = any(item in lat_name_list for item in list_dimensions)
        #check_lon = any(item in lat_name_list for item in list_dimensions)
        check_lat = False
        for m in list_dimensions:
            for n in lat_name_list:
                if m == n:
                    check_lat = True
                    lat_name = m
        if check_lat is False:
            raise ValueError('Cannot find latitude. Names should be either of "lat","latitude" or "y"')

        check_lon=False
        for m in list_dimensions:
            for n in lon_name_list:
                if m == n:
                    check_lon = True
                    lon_name = m
        if check_lon is False:
            raise ValueError('Cannot find longitude. Names should be either of "lon","longitude" or "x"')

        res1 = [] # for storing the monthwise data
        # for each of the month
        for mon in np.arange(1,13):
            X1 = X.sel(time=X['time.month']==mon);
            Y1 = Y.sel(time=Y['time.month']==mon);
            Z1 = Z.sel(time=Z['time.month']==mon);

            lons = X1[lon_name].values;
            lats = X1[lat_name].values;
            print('Obs')
            print(lons);
            print(lats);
            print('Model');
            print(Y1['lon'].values);
            print(Y1['lat'].values);
            print('Future');
            print(Z1['lon'].values);
            print(Z1['lat'].values);
            res = np.empty((len(Z1['time']),len(Z1[lon_name]),len(Z1[lat_name])));

            for loncnt,longitude in enumerate(lons):
                for latcnt,latitude in enumerate(lats):
                    obs_data = X1.sel(lon=longitude,lat=latitude,method='nearest',tolerance=0.001).values;
                    obs_data_all_nan_flag = np.isnan(obs_data).all();

                    hind_data = Y1.sel(lon=longitude,lat=latitude,method='nearest',tolerance=0.001).values;
                    hind_data_all_nan_flag = np.isnan(hind_data).all();

                    fut_data = Z1.sel(lon=longitude,lat=latitude,method='nearest',tolerance=0.001).values;
                    fut_data_all_nan_flag = np.isnan(fut_data).all();

                    flag=obs_data_all_nan_flag or hind_data_all_nan_flag or fut_data_all_nan_flag

                    if flag:
                        corr_data = np.empty(fut_data.shape);
                        corr_data[:]=np.nan;
                    else:
                        corr_data = self.qm(obs_data,hind_data,fut_data,"aurtherlike",correction_type)

                    res[:,loncnt,latcnt] = corr_data;
            new_dims = ('time',lon_name,lat_name)
            res_xr = xr.DataArray(res,coords=Z1.coords,dims=new_dims)
            res1.append(res_xr)

        DScorr = xr.concat(res1,dim='time').sortby('time');
        DScorr.name = var_name;
        DScorr=DScorr.assign_attrs({'title':'Bias corrected using quantile mapping'});
        fut_dims = DSfut.dims;
        DScorr=DScorr.transpose(fut_dims[0],fut_dims[1],fut_dims[2]);
        return DScorr

    def smoothen_clim_fft(self,climdata,varname,nhar=3):
        """
        Uses the fast fourier transform to smoothen the daily climatology from
        from the clim data. Upto nhar harmonics are retained. Default is upto
        3rd harmonics.
        This funtions uses xarray and xrft.

        Parameters
        ----------
        climdata : dataset or dataarray with only one variable varname
            -Gridded datafile in netcdf format or other format compatible with xrray
            -Has only one variable with varname like pr, tas, tasmax etc
        varname : string
            name of the variable
        nhar : integer
            number of harnomics to be retained

        Returns
        -------
        fft_climatology: dataarray
            -fast fourier transformed daily climatology

        """
        # computing the climatology (long term daily average)
        if isinstance(climdata,xr.core.dataarray.Dataset):
            climdata = climdata[varname].copy();

        climatology=climdata.groupby('time.dayofyear').mean('time');

        # Get mask for missing or fill areas
        mask_missing = climatology.sel(dayofyear=1).copy();
        mask_missing = xr.where(np.isnan(mask_missing),True,False);
        mask_missing = mask_missing.drop('dayofyear');

        # since xrft module cannot process with nan values,
        # For the missing and fill values converting all the nan values to -9999,
        # Ensure that the values are filled and no nan values except for mask area
        day_oclimo = climatology.fillna(-999999);

        # fast fourier transformed daily climatology
        fft_day_oclimo = xrft.fft(day_oclimo, dim="dayofyear", true_phase=True, true_amplitude=True);
        #print(fft_day_oclimo);

        # number of days in the daily climatology;
        ndays=day_oclimo.dayofyear.size;
        if ndays%2 == 0:
            freq_lags=ndays/2+1;
        else:
            freq_lags=int(ndays/2)+1;

        # selecting upto the nhar(third) harmonics
        A=fft_day_oclimo.sel(freq_dayofyear=slice(0,np.max(fft_day_oclimo.freq_dayofyear))).real;
        A = np.abs(A);
        dimof_freq = A.dims.index("freq_dayofyear");
        Asort = np.sort(A,axis=dimof_freq)[::-1]; # axis=0 is time;

        # selecting for only for the 3rd order harmonics;
        # which is greater than the 4th position sorted values of A
        index_harmonics = xr.DataArray(Asort[nhar,:,:],
                         coords={'lat': day_oclimo.lat, 'lon': day_oclimo.lon},
                         dims=['lat', 'lon'])
        # retainingg only upto nhar harmonics and setting all other to zero
        fft_day_oclimo_nhar = fft_day_oclimo.where(np.abs(fft_day_oclimo.real)> index_harmonics,other=0);

        # getting inverse fft from the refined fft series
        ifft_day_oclimo_nharmonics = xrft.ifft(fft_day_oclimo_nhar, dim="freq_dayofyear", true_phase=True, true_amplitude=True,lag=freq_lags)
        #
        # Set all the negative values to zero in case of precipitation;
        if varname.lower() in ['pr','precip','p','prcp','tp','precipitation']:
            ifft_day_oclimo_nharmonics = ifft_day_oclimo_nharmonics.where(ifft_day_oclimo_nharmonics>0,0)

        # Replace masked area by nan
        ifft_day_oclimo_nharmonics = ifft_day_oclimo_nharmonics.where(~mask_missing,other=np.nan);

        climatology_fft = ifft_day_oclimo_nharmonics.real.round(3); # get only the real parts
        climatology_fft = climatology_fft.rename(varname); #make sure that variable name is varname
        # fft_day_oclimo,fft_day_oclimo_nhar,ifft_day_oclimo_nharmonics
        return climatology_fft

    def OnLoadObsHistorical(self,event):
        """Open a file"""
        self.dirname = ''
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        dlg = wx.FileDialog(self, "Choose observation data file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            self.ObsHistoricalPath.SetValue(f)
            # display this in file control
            ObsHistorical = xr.open_dataset(f,engine="netcdf4")
            print(ObsHistorical);
            print("Variables are:");
            print(list(ObsHistorical.keys()))
            self.ObsHistoricalData = ObsHistorical;
            self.logger3.SetDefaultStyle(wx.TextAttr(wx.Colour(0,145,0)))
            #print(self.ObsHistoricalData)
            self.logger3.SetDefaultStyle(self.logger3_ds);
            self.selectedObsVarList = list(ObsHistorical.keys());
            for i in list(ObsHistorical.keys()):
                self.combo_obsvar_declare.Append(i)
            ObsHistorical.close()
        dlg.Destroy()

    def OnLoadModelHindcastData(self,event):
        """Open a file"""
        self.dirname = ''
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        dlg = wx.FileDialog(self, "Choose model hindcast data file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            self.ModelHindcastPath.SetValue(f)
            # display this in file control
            ModelHindcast = xr.open_dataset(f,engine="netcdf4")
            print(ModelHindcast);
            print("Variables are:");
            print(list(ModelHindcast.keys()))
            self.ModelHindcastData = ModelHindcast;
            self.logger3.SetDefaultStyle(wx.TextAttr(wx.Colour(0,145,0)))
            self.logger3.SetDefaultStyle(self.logger3_ds)
            self.selectedModelVarList = list(ModelHindcast.keys());
            for i in list(ModelHindcast.keys()):
                self.combo_modelvar_declare.Append(i)
            ModelHindcast.close();
        dlg.Destroy()

    def OnLoadModelFutureData(self,event):
        """Open a file"""
        self.dirname = ''
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        dlg = wx.FileDialog(self, "Choose model future data file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            self.ModelFuturePath.SetValue(f)
            # display this in file control
            ModelFuture = xr.open_dataset(f,engine="netcdf4")
            print(ModelFuture);
            print("Variables are:");
            print(list(ModelFuture.keys()))
            self.ModelFutureData = ModelFuture;
            ModelFuture.close();
        dlg.Destroy()

    def Oncombo_obsvar_declare(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        id1 = self.combo_obsvar_declare.GetSelection()
        self.ObsVarname = self.selectedObsVarList[id1]
        print("Variable is {}.".format(self.ObsVarname))

    def Oncombo_modelvar_declare(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        id1 = self.combo_modelvar_declare.GetSelection()
        self.ModelVarname = self.selectedModelVarList[id1]
        print("Variable is {}.".format(self.ModelVarname))

    def OnWetThresholdBox(self,event):
        n = float(self.WetThresholdBox.GetLineText(0))
        self.wet_threshold = n
        print("Precipitation threshold set to: {}".format(self.wet_threshold))

    def Oncombo_regrideng_declare(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        id1 = self.combo_regrideng_declare.GetSelection()
        self.SelectedRegridEng = self.RegridEngList[id1]
        print("Selected Regrid Engine is {}.".format(self.SelectedRegridEng))

    def Oncombo_regridmethod_declare(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        id1 = self.combo_regridmethod_declare.GetSelection()
        self.SelectedRegridMethod = self.RegridEngMethod[id1]
        print("Selected Regrid Engine is {}.".format(self.SelectedRegridMethod))

    def OnRegrid(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        print(self.wet_threshold)

        obs = self.sanitize_climdata(self.ObsHistoricalData,
                                     self.ObsVarname,
                                     self.ModelVarname,
                                     threshold=self.wet_threshold);
        model = self.sanitize_climdata(self.ModelHindcastData,
                                       self.ModelVarname,
                                       self.ModelVarname,
                                       threshold=self.wet_threshold);
        print('model dimensions')
        print(model.dims)
        print()
        print('obs dimensions')
        print(obs.dims)
        model_dims = model.dims;
        obs=obs.transpose(model_dims[0],model_dims[1],model_dims[2]); #arranging obs according to model dims
        regrid_method=self.SelectedRegridMethod
        obs_at_gcmres = self.Regridding(obs,model,regrid_method);
        self.obs_at_gcmres = obs_at_gcmres;
        print(self.obs_at_gcmres);
        print('Saving file: Output directory:')
        print(os.getcwd())
        print('File name is obs_at_gcmres.nc')
        obs_at_gcmres.to_netcdf(os.path.join(os.getcwd(),'obs_at_gcmres.nc'),
                                encoding={self.ModelVarname: {'dtype': 'float32','_FillValue':np.nan}});
        del obs_at_gcmres
        pass

    def Oncombo_QMmethod_declare(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        id1 = self.combo_QMmethod_declare.GetSelection()
        self.SelectedQMmethod = self.QMmethodlist[id1]
        print("Selected QM method is {}.".format(self.SelectedQMmethod))

    def OnOutputDirButton(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        """Open a file"""
        self.OutputDir = ''
        dlg = wx.FileDialog(self, "Input filename and location",defaultFile = "bias_corrected.nc", wildcard="netcdf (*.nc)|*.nc", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            self.OutputDir = dlg.GetPath()
            self.OutputPath.SetValue(self.OutputDir)
        dlg.Destroy()

    def OnPerformQM(self,event):
        """Open a file"""
        self.dirname = ''
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        DSobs = self.sanitize_climdata(self.obs_at_gcmres,
                                     self.ModelVarname,
                                     self.ModelVarname,
                                     threshold=self.wet_threshold);
        DShind = self.sanitize_climdata(self.ModelHindcastData,
                                       self.ModelVarname,
                                       self.ModelVarname,
                                       threshold=self.wet_threshold);
        DSfut = self.sanitize_climdata(self.ModelFutureData,
                                       self.ModelVarname,
                                       self.ModelVarname,
                                       threshold=self.wet_threshold);

        DScorrected = self.qm_monthwise(DSobs, DShind, DSfut,
                                        self.ModelVarname,
                                        self.SelectedQMmethod);
        self.bias_corrected_fut_model = DScorrected;
        print('Bias corrected file:')
        print(self.bias_corrected_fut_model);
        print('Saving file: Output directory:')
        print(self.OutputDir)
        #print('File name is bias_corrected.nc')
        DScorrected.to_netcdf(os.path.join(self.OutputDir),
                                encoding={self.ModelVarname: {'dtype': 'float32','_FillValue':np.nan}});
        del DSobs, DShind, DSfut, DScorrected

    def OnProcess_obs_climatology(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        obs = self.sanitize_climdata(self.ObsHistoricalData,
                                     self.ObsVarname,
                                     self.ModelVarname,
                                     threshold=self.wet_threshold);
        DSfut = self.sanitize_climdata(self.ModelFutureData,
                                       self.ModelVarname,
                                       self.ModelVarname,
                                       threshold=self.wet_threshold);
        model_dims = DSfut.dims;
        obs=obs.transpose(model_dims[0],model_dims[1],model_dims[2]);
        self.obs_climatology  = self.smoothen_clim_fft(obs,self.ModelVarname,nhar=3);
        print(self.obs_climatology)
        print("File saved in")
        print(os.getcwd())
        print( "as obs_climatology.nc")
        self.obs_climatology.to_netcdf(os.path.join(os.getcwd(),'obs_climatology.nc'),
                                encoding={self.ModelVarname: {'dtype': 'float32','_FillValue':np.nan}});
        del obs
        pass

    def OnRegrid2(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        obs = self.sanitize_climdata(self.obs_climatology,
                                     self.ModelVarname,
                                     self.ModelVarname,
                                     threshold=self.wet_threshold);
        model = self.sanitize_climdata(self.ModelHindcastData,
                                       self.ModelVarname,
                                       self.ModelVarname,
                                       threshold=self.wet_threshold);
        regrid_method=self.SelectedRegridMethod
        obs_clim_at_gcmres = self.Regridding(obs,model,regrid_method);
        self.obs_clim_at_gcmres = obs_clim_at_gcmres;
        print(self.obs_clim_at_gcmres);
        print('Saving file: Output directory:')
        print(os.getcwd())
        print('File name is obs_clim_at_gcmres.nc')
        obs_clim_at_gcmres.to_netcdf(os.path.join(os.getcwd(),'obs_clim_at_gcmres.nc'),
                                encoding={self.ModelVarname: {'dtype': 'float32','_FillValue':np.nan}});
        del obs_clim_at_gcmres
        pass

    def OnProcessFactors(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        DSfut = self.bias_corrected_fut_model;

        print('Bias corrected future data:')
        print(DSfut);
        print();
        print('Obs_climatology at model resolution:')
        print(self.obs_clim_at_gcmres);
        print()
        print(DSfut.time)

        # Get daily climatology;
        day_oclimo = self.obs_clim_at_gcmres;

        store1 = np.empty(DSfut.shape);
        pdDate = DSfut.indexes['time'];
        for j,i in enumerate(pdDate):
            try:
                # If the pdDate is cftime then this will work
                store1[j,:,:] = day_oclimo.sel(dayofyear=i.dayofyr,method='nearest').values
            except:
                # If the pdDate is pandas datatimeinfex then this will work
                store1[j,:,:] = day_oclimo.sel(dayofyear=i.dayofyear,method='nearest').values

        day_oclimo_filled = xr.DataArray(store1,
                                         coords=DSfut.coords,
                                         dims=DSfut.dims)

        # get the mask where day_oclimo has missing values;
        mask_missing = day_oclimo.isnull();
        mask_missing = mask_missing.drop('dayofyear');

        # mask_missing_for_future
        mask_notmissing_fut = DSfut.notnull();
        mask_zeros_fut = xr.where(DSfut <= 0,True,False)

        # set all the zero values of day_oclimo to -9999 for factors computation otherwise
        # it will give infinity values
        # calculate the factors

        method = self.SelectedQMmethod;
        # additive and multiplicative
        if method == "additive":
            factors = DSfut - day_oclimo_filled;
            factors = factors.drop('dayofyear');
            if isinstance(factors,xr.core.dataarray.Dataset):
                factors = factors.to_array();

        elif method == "multiplicative":
            # initialising the factors
            # put nan and others as same while zeros as -9999;
            day_oclimo_filled = day_oclimo_filled.where(
                (day_oclimo_filled != 0) | np.isnan(day_oclimo_filled),
                other = -9999);

            day_oclimo.to_netcdf(os.path.join(os.getcwd(),'day_oclimo_1.nc'),
                                    encoding={self.ModelVarname: {'dtype': 'float32','_FillValue':np.nan}});

            factors = DSfut / day_oclimo_filled;
            # This will result in dataarray instead of dataset.
            # caution this can give large factoral values when the daily climatological values
            # are very less (less than 1)
            # This has been taken care for most of case by setting pr < 0.25 as zeros
            factors = factors + 0; # this will remove negative zeros

            # if the factors is dataaary (like pandas series) conveting it into dataset (dataframe)
            if isinstance(factors,xr.core.dataarray.Dataset):
                factors = factors.to_array();

            #
            factors = xr.where(mask_zeros_fut,0,factors);
            factors = xr.where(factors <= 0,0,factors);
            factors = factors.where(mask_notmissing_fut,np.nan);

        # linearly interpolation along time if any five consecutive missing values along time dimension
        factors = factors.interpolate_na(dim="time", limit=5, method="linear", fill_value="extrapolate")
        factors.lat.attrs = DSfut.lat.attrs;
        factors.lon.attrs = DSfut.lon.attrs;
        factors.time.attrs = DSfut.time.attrs;
        factors.name = self.ModelVarname;
        self.factors = factors;
        print()
        print('Factors file:')
        print(factors)
        print(self.factors);
        print('Saving file: Output directory:')
        print(os.getcwd())
        print('File name is factors_at_gcmres.nc');
        factors.to_netcdf(os.path.join(os.getcwd(),'factors_at_gcmres.nc'),
                                encoding={self.ModelVarname: {'dtype': 'float32','_FillValue':np.nan}});
        print()
        pass

    def OnProcessFactors2(self,event):
        """ Interpolate factors at observation resolution """
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        print(self.wet_threshold)
        obs = self.sanitize_climdata(self.obs_climatology,
                                     self.ModelVarname,
                                     self.ModelVarname,
                                     threshold=self.wet_threshold);

        source_res = self.factors;
        target_res = obs;
        print('factors dimensions at model res')
        print(source_res.dims)
        print()
        print('factors dimensions at obs res')
        print(target_res.dims)
        regrid_method='BIL';
        factors_at_obsres = self.Regridding(source_res,target_res,regrid_method);
        self.factors_at_obsres = factors_at_obsres;
        print(self.factors_at_obsres);
        print('Saving file: Output directory:')
        print(os.getcwd())
        print('File name is factors_at_obsres.nc')
        factors_at_obsres.to_netcdf(os.path.join(os.getcwd(),'factors_at_obsres.nc'),
                                encoding={self.ModelVarname: {'dtype': 'float32','_FillValue':np.nan}});
        pass

    def OnGetBCSDdata(self,event):
        """ Embed factors into the observation to get SD data """
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        factors_at_obsres = self.factors_at_obsres;
        factors_dims = factors_at_obsres.dims
        obs_climatology = self.obs_climatology;
        obs_climatology = obs_climatology.transpose('dayofyear',factors_dims[1],factors_dims[2]);
        print()
        #print(" factors at obs res ")
        #print(factors_at_obsres);
        #print(factors_at_obsres.coords);
        #print()
        #print("Observed climatology at obs res")
        #print(obs_climatology)
        #print(obs_climatology.dims)
        #print()

        store1 = np.empty(factors_at_obsres.shape);
        pdDate = factors_at_obsres.indexes['time'];
        for j,i in enumerate(pdDate):
            try:
                # If the pdDate is cftime then this will work
                store1[j,:,:] = obs_climatology.sel(dayofyear=i.dayofyr,method='nearest').values
            except:
                # If the pdDate is pandas datatimeinfex then this will work
                store1[j,:,:] = obs_climatology.sel(dayofyear=i.dayofyear,method='nearest').values

        obs_climatology_filled = xr.DataArray(store1,
                                                 coords=factors_at_obsres.coords,
                                                 dims=factors_at_obsres.dims)
        #print(obs_climatology_filled);
        #print(obs_climatology_filled.dims);

        method = self.SelectedQMmethod;
        # additive and multiplicative
        if method == "additive":
            result_BCSD = factors_at_obsres + obs_climatology_filled;
        elif method == "multiplicative":
            result_BCSD = factors_at_obsres * obs_climatology_filled;
        self.result_BCSD = result_BCSD;

        print()
        print('BCSD result:')
        print(result_BCSD)
        pass

    def OnSaveBCSDdata(self,event):
        sys.stdout = self.logger3
        sys.stderr = self.logger3
        result_BCSD = self.result_BCSD;
        with wx.FileDialog(self, "Input filename and location",
                           defaultFile = "BCSD_result.nc",
                           wildcard="netcdf (*.nc)|*.nc",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind
            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                result_BCSD.name = self.ModelVarname;
                result_BCSD.to_netcdf(pathname,
                                      encoding={self.ModelVarname: {'dtype': 'float32','_FillValue':np.nan}});
                print("File save as:")
                print(pathname);
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)
        pass

    def OnResetAll1(self,event):
        self.ObsHistoricalData = None
        self.ObsVarname = None
        self.ModelHindcastData = None
        self.ModelVarname = None
        self.ModelFutureData = None
        self.givenVarname = None
        self.RegridEngList = ['CDO','XE REGRIDDER'];
        self.SelectedRegridEng = None
        self.RegridEngMethod = ['NN','BIL','CON'];
        self.SelectedRegridMethod = None
        self.wet_threshold = 1.0
        self.QMmethodlist = ['multiplicative','additive'];
        self.QMwindowlist = ['monthly'];
        self.SelectedQMmethod = None;
        self.DScorr = None;
        self.OutputDir = None
        self.factors = None;
        self.result_BCSD = None;

        self.logger3.SetValue("")

    def OnClearLogger(self,event):
        self.logger3.SetValue("")

#%%
###-----------------------------------###-----------------------------------###

class RV_top_Panel(wx.Panel):
    """"""
    def __init__(self, parent, id=-1, dpi=None, **kwargs):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent, id=id, style = wx.BORDER_SUNKEN,**kwargs)
        self.figure = mpl.figure.Figure(figsize=(4.5,0.3))
        self.axes = self.figure.add_subplot(111)
        self.axes.grid(True,'major',color = (0.95,0.95,0.95))
        self.canvas = FigureCanvas(self,-1,self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, flag = wx.ALL|wx.ALIGN_TOP, border = 5) #wx.EXPAND)
        #sizer.Add(self.canvas, 1, flag = wx.ALIGN_CENTER_VERTICAL, border = 5)
        sizer.AddSpacer(2)
        sizer.Add(self.toolbar, 0, wx.LEFT| wx.EXPAND)
        self.SetSizer(sizer)


class RV_bottom_Panel(wx.Panel):
    """"""
    def __init__(self, parent):
        """Constructor"""
        ch1 = ['Daily', 'Annual sum', 'Annual mean', \
               'Monthly sum', 'Monthly mean',\
               'AverageMonthly(sums)','AverageMonthly(means)']
        ch2 = ['Daily', 'Annual sum', 'Annual mean', \
               'Monthly sum', 'Monthly mean',\
               'AverageMonthly(sums)','AverageMonthly(means)']
        self.plot_choices = {'Time series': ch1,
                             'Scatter X-Y': ch2,}
        wx.Panel.__init__(self, parent=parent,style = wx.BORDER_SUNKEN)

        #Setting the sizer of bottomP
        sizer1 = wx.GridBagSizer(hgap=0, vgap=0)

        # Load file 1
        self.loadfile1 = wx.Button(self,label = 'Load file 1')
        sizer1.Add(self.loadfile1, pos = (0,0),flag = wx.ALL|wx.EXPAND,border = 5)

        self.file1path = wx.TextCtrl(self,value = "")
        sizer1.Add(self.file1path, pos = (0,1), flag = wx.EXPAND|wx.ALL, border = 5)

        # load file 2
        self.loadfile2 = wx.Button(self,label = 'Load file 2')
        sizer1.Add(self.loadfile2, pos = (1,0),flag = wx.ALL|wx.EXPAND,border = 5)

        self.file2path = wx.TextCtrl(self,value = "")
        sizer1.Add(self.file2path, pos = (1,1), flag = wx.EXPAND|wx.ALL, border = 5)

        # Process
        self.process = wx.Button(self,label = 'Process files')
        sizer1.Add(self.process, pos = (2,0),flag = wx.ALL|wx.EXPAND,border = 5)

        #xxxx
        # Select plotting types
        self.text0 = wx.StaticText(self, label = "Select type ")
        sizer1.Add(self.text0, pos = (0, 2), flag = wx.ALL, border = 5)

        # Creating choices
        choices0 = list(self.plot_choices.keys())
        self.select_type = wx.ComboBox(self,id=wx.ID_ANY,choices = choices0, \
                                                    style = wx.LB_MULTIPLE)
        sizer1.Add(self.select_type, pos = (0, 3), flag = wx.ALL|wx.EXPAND, border = 5)

        # Select what to plot
        self.text1 = wx.StaticText(self, label = "prop X")
        sizer1.Add(self.text1, pos = (1, 2), flag = wx.ALL, border = 5)

        # Creating choices
        choices1 = [] #This is the states for number of states
        self.select_prop = wx.ComboBox(self,id=wx.ID_ANY,choices = choices1, \
                                                    style = wx.LB_MULTIPLE)
        sizer1.Add(self.select_prop, pos = (1, 3), flag = wx.ALL|wx.EXPAND, border = 5)

        # Select what to plot
        self.text1a = wx.StaticText(self, label = "prop Y")
        sizer1.Add(self.text1a, pos = (2, 2), flag = wx.ALL, border = 5)

        # Creating choices
        choices1a = [] #This is the states for number of states
        self.select_propY = wx.ComboBox(self,id=wx.ID_ANY,choices = choices1a, \
                                                    style = wx.LB_MULTIPLE)
        sizer1.Add(self.select_propY, pos = (2, 3), flag = wx.ALL|wx.EXPAND, border = 5)


        # Select X variable for plotting
        self.text2 = wx.StaticText(self, label = "Select X")
        sizer1.Add(self.text2, pos = (3, 2), flag = wx.ALL, border = 5)

        # Creating choices
        choices2 = [] #This is the states for number of states
        self.selectX = wx.ComboBox(self,id=wx.ID_ANY,choices = choices2, \
                                                    style = wx.LB_MULTIPLE)
        sizer1.Add(self.selectX, pos = (3, 3), flag = wx.ALL|wx.EXPAND, border = 5)

        # Select X variable for plotting
        self.text3 = wx.StaticText(self, label = "Select Y")
        sizer1.Add(self.text3, pos = (4, 2), flag = wx.ALL, border = 5)

        # Creating choices
        choices3 = [] #This is the states for number of states
        self.selectY = wx.ComboBox(self,id=wx.ID_ANY,choices = choices3, \
                                                    style = wx.LB_MULTIPLE)
        sizer1.Add(self.selectY, pos = (4, 3), flag = wx.ALL|wx.EXPAND, border = 5)

        # Creating plot buttons
        self.plot_button1 = wx.Button(self,label = 'Plot')
        sizer1.Add(self.plot_button1,pos = (0,4),flag = wx.ALL|wx.EXPAND,border = 5)

        # Creating labelling box
        # Select X label
        self.text4 = wx.StaticText(self, label = "x-axis label")
        sizer1.Add(self.text4, pos = (1, 4), flag = wx.ALL, border = 5)

        # Select Y label
        self.text5 = wx.StaticText(self, label = "y-axis label")
        sizer1.Add(self.text5, pos = (2, 4), flag = wx.ALL, border = 5)

        #Create xlabel control box
        self.xlabelbox = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        sizer1.Add(self.xlabelbox, pos = (1,5), flag = wx.EXPAND|wx.ALL, border = 5)
        self.xlabelbox.Disable()

        #Create ylabel control box
        self.ylabelbox = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        sizer1.Add(self.ylabelbox, pos = (2,5), flag = wx.EXPAND|wx.ALL, border = 5)
        self.ylabelbox.Disable()

        # Select legend label
        self.text6 = wx.StaticText(self, label = "legend")
        sizer1.Add(self.text6, pos = (3, 4), flag = wx.ALL, border = 5)

        #Create ylabel control box
        self.legendbox = wx.TextCtrl(self,value = "", style = wx.TE_PROCESS_ENTER)
        # Add to the sizer grid
        sizer1.Add(self.legendbox, pos = (3,5), flag = wx.EXPAND|wx.ALL, border = 5)

        # Create radio button for plot refresher
        self.plot_refresh = wx.CheckBox(self,label = "Refresh plot")
        sizer1.Add(self.plot_refresh, pos = (0,5), flag = wx.EXPAND|wx.ALL, border = 5)
        #self.plot_refresh.SetBackgroundColour(wx.Colour(240, 240, 240))

        # Plot button for testing
        self.plot_button = wx.Button(self,label = 'Test Plot')
        sizer1.Add(self.plot_button,pos = (3,0),flag = wx.ALL|wx.EXPAND,border = 5)

        # Creating plot buttons
        self.plot_button2 = wx.Button(self,label = 'Clear Plot')
        sizer1.Add(self.plot_button2,pos = (0,6),flag = wx.ALL|wx.EXPAND,border = 5)

        # Creating plot buttons
        self.plot_button3 = wx.Button(self,label = 'Clear All')
        sizer1.Add(self.plot_button3,pos = (1,6),flag = wx.ALL|wx.EXPAND,border = 5)

        # settinf sizer
        self.SetSizer(sizer1)

class ResultViewerPanel(wx.Panel):
    """"""
    #----------------------------------------------------------------------
    def __init__(self, parent):
        self.data1 = pd.DataFrame() #empty dataframe
        self.data2 = pd.DataFrame()
        self.mergeddata = pd.DataFrame()
        self.data_dict = {} #empty dictionary
        """Constructor"""
        wx.Panel.__init__(self, parent)

        self.sp = wx.SplitterWindow(self,style = wx.SP_BORDER)
        self.topP = RV_top_Panel(self.sp)
        self.bottomP = RV_bottom_Panel(self.sp)

        self.bottomP.plot_button.Bind(wx.EVT_BUTTON, self.showplot)
        self.bottomP.loadfile1.Bind(wx.EVT_BUTTON,self.OnLoadFile1)
        self.bottomP.loadfile2.Bind(wx.EVT_BUTTON,self.OnLoadFile2)
        self.bottomP.process.Bind(wx.EVT_BUTTON,self.OnProcess)
        self.bottomP.select_type.Bind(wx.EVT_COMBOBOX, self.OnSelectType)
        self.bottomP.plot_button1.Bind(wx.EVT_BUTTON,self.OnPlotButton1)
        self.bottomP.xlabelbox.Bind(wx.EVT_TEXT, self.OnXlabelBox)
        self.bottomP.ylabelbox.Bind(wx.EVT_TEXT, self.OnYlabelBox)
        #self.bottomP.legendbox.Bind(wx.EVT_TEXT, self.OnLegendBox)
        self.bottomP.plot_button2.Bind(wx.EVT_BUTTON,self.OnClear)
        self.bottomP.plot_button3.Bind(wx.EVT_BUTTON,self.OnClearAll)

        # split the window
        self.sp.SplitHorizontally(self.topP, self.bottomP)
        self.sp.SetMinimumPaneSize(400)
        self.sp.SetSashGravity(0.7)
        self.Show(True)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sp, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def showplot(self,event):
        X = [1,2,3,4]
        Y = [1,4,9,16]
        self.topP.axes.clear()
        self.topP.axes.plot(X, Y)
        self.topP.axes.set_xlabel('Number')
        self.topP.canvas.draw()
#        textmsg = """Test"""
#        dlg = wx.MessageDialog(self,textmsg,"TEst ",wx.OK)
#        dlg.ShowModal() #Show the messagebox
#        dlg.Destroy()

    def OnLoadFile1(self,event):
        """Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose data file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            self.bottomP.file1path.SetValue(f)
            # display this in file control
            MainData = pd.read_csv(f,header = 0,parse_dates=True)
            MainData.index.rename('id',inplace=True)
            MainData.Date = pd.to_datetime(MainData.Date, format="%Y-%m-%d")
            cols=[i for i in MainData.columns if i not in ["Date","date","year","month","day"]]
            new_name = {}
            for col in cols:
                MainData[col]=pd.to_numeric(MainData[col],errors='coerce')
                new_name[col] = 'file1_' + col
            # self.control.SetValue(f.read()) #This is showing data on the logger
            new_data = MainData.copy()
            new_data.rename(columns = new_name, inplace = True)
            self.data1 = new_data
            #print("Data loaded and convert into pandas dataframe!")
            #print("Its columns are: {}".format(self.MainData.columns))
        dlg.Destroy()

    def OnLoadFile2(self,event):
        """Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose data file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = os.path.join(self.dirname, self.filename)
            self.bottomP.file2path.SetValue(f)
            # display this in file control
            MainData = pd.read_csv(f,header = 0,parse_dates=True)
            MainData.index.rename('id',inplace=True)
            MainData.Date = pd.to_datetime(MainData.Date, format="%Y-%m-%d")
            cols=[i for i in MainData.columns if i not in ["Date","date","year","month","day"]]
            new_name = {}
            for col in cols:
                MainData[col]=pd.to_numeric(MainData[col],errors='coerce')
                new_name[col] = 'file2_' + col
            # self.control.SetValue(f.read()) #This is showing data on the logger
            new_data = MainData.copy()
            new_data.rename(columns = new_name, inplace = True)
            self.data2 = new_data
            #print("Data loaded and convert into pandas dataframe!")
            #print("Its columns are: {}".format(self.MainData.columns))
        dlg.Destroy()

    def OnProcess(self,event):
        data_list = []
        flag1 = not self.data1.empty
        if flag1 == True:
            self.data1_dict = wg.convert2singlesite(self.data1)
            data_list += list(self.data1_dict.values())

        flag2 = not self.data2.empty
        if flag2 == True:
            self.data2_dict = wg.convert2singlesite(self.data2)
            data_list += list(self.data2_dict.values())

        if (flag1 | flag2) == False:
            textmsg = """Load the file first!"""
            dlg = wx.MessageDialog(self,textmsg,"Load file",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy()
        else:
            #df = pd.concat([self.data1,self.data2],axis = 1).copy()
            #df = df.loc[:,~df.columns.duplicated()]
            #self.mergeddata = df.copy()
#            print(self.data1.columns)
#            print(self.data2.columns)
#            print(self.mergeddata)
#            print(self.mergeddata.columns)
#            print(self.mergeddata.dtypes)
            #self.data_dict = wg.convert2singlesite(self.mergeddata)
            display_items = []
            for count,datas in enumerate(data_list):
                    display_items.append(datas.name)
                    self.data_dict[datas.name] = datas

            #self.data_dict['Date'] = self.mergeddata['Date']
            self.bottomP.selectX.Clear()
            for j in display_items:
                self.bottomP.selectX.Append(j)
                self.bottomP.selectY.Append(j)

    def OnSelectType(self,event):
        nId = self.bottomP.select_type.GetStringSelection()
        #print(nId)
        choices = self.bottomP.plot_choices[nId]
        self.bottomP.select_prop.Clear()
        self.bottomP.select_propY.Clear()
        self.bottomP.selectX.SetSelection(-1)
        self.bottomP.selectY.SetSelection(-1)
        for i in choices:
            self.bottomP.select_prop.Append(i)
            self.bottomP.select_propY.Append(i)
        if nId in ["Time series"]:
            self.bottomP.selectY.Disable()
            self.bottomP.select_propY.Disable()
        else:
            self.bottomP.selectY.Enable()
            self.bottomP.select_propY.Enable()

    def OnPlotButton1(self,event):
        # Get the settings from the combo box
        n_type = self.bottomP.select_type.GetStringSelection() # return the text
        n_prop = self.bottomP.select_prop.GetStringSelection() # returns the interger
        n_propY = self.bottomP.select_propY.GetStringSelection() #
        n_data1 = self.bottomP.selectX.GetStringSelection()  # returnt the name of data
        n_data2 = self.bottomP.selectY.GetStringSelection()

        if (n_type == ''):
            textmsg = """Select plot type first! """
            dlg = wx.MessageDialog(self,textmsg,"Reminder",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy()
            self.bottomP.xlabelbox.Disable()
            self.bottomP.ylabelbox.Disable()

        elif (n_prop == '') & (n_propY == ''):
            textmsg = """Select options to plot first! """
            dlg = wx.MessageDialog(self,textmsg,"Reminder",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy()
            self.bottomP.xlabelbox.Disable()
            self.bottomP.ylabelbox.Disable()

        elif (n_data1 == '') & (n_data2 == ''):
            textmsg = """Select data to plot first! """
            dlg = wx.MessageDialog(self,textmsg,"Reminder",wx.OK)
            dlg.ShowModal() #Show the messagebox
            dlg.Destroy()
            self.bottomP.xlabelbox.Disable()
            self.bottomP.ylabelbox.Disable()

        elif n_type in ['Time series']:
            try:
                Xwg = self.data_dict[n_data1]
                X_df = Xwg.genResampledTimeSeries(n_data1,n_prop)
                self.bottomP.xlabelbox.Enable()
                self.bottomP.ylabelbox.Enable()
                self.bottomP.selectY.SetSelection(-1)
                self.bottomP.selectY.Disable()
                self.bottomP.select_propY.SetSelection(-1)
                self.bottomP.select_propY.Disable()
                refresher = self.bottomP.plot_refresh.IsChecked()
                if refresher == True:
                    self.topP.axes.clear()
                    self.topP.axes.grid(True,'major',color = (0.95,0.95,0.95))
                #self.topP.axes.plot(X_df.index, X_df[n_data1])
                self.topP.axes.plot(X_df.index, X_df[n_data1],label = self.bottomP.legendbox.GetLineText(0))
                self.topP.axes.legend()
                self.topP.axes.set_axisbelow(True)
                self.topP.canvas.draw()
            except:
                textmsg = """Either or both of 'prop X' and 'Select X' are missing!"""
                dlg = wx.MessageDialog(self,textmsg,"Reminder",wx.OK)
                dlg.ShowModal() #Show the messagebox
                dlg.Destroy()
                self.bottomP.xlabelbox.Disable()
                self.bottomP.ylabelbox.Disable()

        elif n_type not in ['Time series']:
            try:
                Xwg = self.data_dict[n_data1]
                Ywg = self.data_dict[n_data2]
                X_df = Xwg.genResampledTimeSeries(n_data1,n_prop)
                Y_df = Ywg.genResampledTimeSeries(n_data2,n_propY)
                self.bottomP.xlabelbox.Enable()
                self.bottomP.ylabelbox.Enable()
                refresher = self.bottomP.plot_refresh.IsChecked()
                if refresher == True:
                    self.topP.axes.clear()
                    self.topP.axes.grid(True,'major',color = (0.95,0.95,0.95))
                self.topP.axes.scatter(X_df[n_data1],Y_df[n_data2],label = self.bottomP.legendbox.GetLineText(0))
                self.topP.axes.legend()
                self.topP.axes.set_axisbelow(True)
                self.topP.canvas.draw()
            except:
                textmsg = """Please check the followings:
                             a) Either or all of 'prop X', 'prop Y', 'Select X' and 'Select Y' are missing!
                             b) Dimensions of selected 'prop X' and 'prop Y' mismatched!
                             """
                dlg = wx.MessageDialog(self,textmsg,"Reminder",wx.OK)
                dlg.ShowModal() #Show the messagebox
                dlg.Destroy()
                self.bottomP.xlabelbox.Disable()
                self.bottomP.ylabelbox.Disable()


    def OnXlabelBox(self, event):
        text = self.bottomP.xlabelbox.GetLineText(0)
        self.topP.axes.set_xlabel(text)
        self.topP.canvas.draw()

    def OnYlabelBox(self, event):
        text = self.bottomP.ylabelbox.GetLineText(0)
        self.topP.axes.set_ylabel(text)
        self.topP.canvas.draw()

    def OnLegendBox(self, event):
        #text = self.bottomP.legendbox.GetLineText(0)
        #self.topP.axes.legend([text])
        #self.topP.canvas.draw()
        pass

    def OnClear(self,event):
        self.topP.axes.clear()
        self.topP.axes.grid(True,'major',color = (0.95,0.95,0.95))
        self.topP.canvas.draw()

    def OnClearAll(self,event):
        self.data1 = pd.DataFrame() #empty dataframe
        self.data2 = pd.DataFrame()
        self.mergeddata = pd.DataFrame()
        self.data_dict = {} #empty dictionary

        self.bottomP.file1path.SetValue("")
        self.bottomP.file2path.SetValue("")
        self.bottomP.select_type.SetSelection(-1)
        self.bottomP.select_prop.SetSelection(-1)
        self.bottomP.select_propY.SetSelection(-1)
        self.bottomP.select_prop.Clear()
        self.bottomP.select_propY.Clear()
        self.bottomP.selectX.SetSelection(-1)
        self.bottomP.selectY.SetSelection(-1)
        self.bottomP.selectX.Clear()
        self.bottomP.selectY.Clear()
        self.bottomP.plot_refresh.SetValue(0)
        self.bottomP.xlabelbox.SetValue("")
        self.bottomP.ylabelbox.SetValue("")
        self.bottomP.legendbox.SetValue("")

        self.topP.axes.clear()
        self.topP.axes.grid(True,'major',color = (0.95,0.95,0.95))
        self.topP.canvas.draw()

#%%
if __name__ == "__main__":
    app = []
    app = wx.App(False)
    #app = wit.InspectableApp()
    frame = WGFrame(None,'Weather Generator & Climate Change Scenario Generator for Climate Risk Assessment')
    frame.Centre()
    frame.Show(True)
    app.MainLoop()
    del app

