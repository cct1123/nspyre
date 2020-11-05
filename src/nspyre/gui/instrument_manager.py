#!/usr/bin/env python
"""
This instrument manager is a GUI which can connect to a set of
instrument servers and control the associated devices

Author: Michael Solomon, Jacob Feder
Date: 10/26/2020
"""

# std
import functools
import weakref

# 3rd party
from PyQt5.QtCore import Qt, QProcess, QSize
from PyQt5.QtGui import QFont
from pyqtgraph import SpinBox
from pyqtgraph import exit as pyqtgraph_exit
from pyqtgraph import _connectCleanup as pyqtgraph_connectCleanup
from PyQt5.QtWidgets import QApplication, QComboBox, QLineEdit, QMainWindow, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHeaderView

# nspyre
from nspyre.inserv.gateway import InservGateway
from nspyre.definitions import Q_

###########################
# exceptions
###########################

class InstrumentManagerError(Exception):
    """General InstrumentManagerWidget exception"""
    def __init__(self, msg):
        super().__init__(msg)

###########################
# classes
###########################

class InstrumentManagerWindow(QMainWindow):
    """This is progress, I promise."""
    def __init__(self, gateway, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('NSpyre Instrument Manager')
        #self.setFont(QFont('Helvetica [Cronyx]', 20))
        #self.setStyleSheet('QLabel {font: Helvetica [Cronyx]}')
        #self.setStyleSheet('QTreeWidget {font: 12pt Helvetica [Cronyx]}')
        #self.setStyleSheet('QPushButton {font: Helvetica [Cronyx]}')
        #self.setStyleSheet('QPushButton {font-size: 16pt}')

        # connection to the instrument servers
        self.gateway = gateway
        self._slots = []
        # tree of dictionaries that contains all of the instrument
        # manager GUI elements
        # the top level of the dictionary is the instrument servers
        # the next level is the devices
        # the bottom level is attributes of the devices
        # e.g.               ----------self.gui----------
        #                   /                            \
        #               server1                        server2
        #              /       \                      /       \
        #      sig-gen1         scope1        sig-gen2         laser
        #      /      \        /      \      /        \       /     \
        #   freq     ampl    trig    din[] freq      ampl  lambda  power

        # set main GUI layout
        self.tree = QTreeWidget()
        self.tree.setFont(QFont('Helvetica [Cronyx]', 14))
        self.tree.setColumnCount(2)
        self.tree.setMinimumHeight(self.tree.height())
        #self.tree.setUniformRowHeights(True)
        #self.tree.setHeaderLabels(['Lantz Feat', 'value'])
        #self.tree.setDragEnabled(True)
        # self.tree.setSortingEnabled(True)
        # self.tree.sortByColumn(0, Qt.AscendingOrder)

        # configure the QTreeWidget Header
        header = self.tree.header()
        header.setHidden(True)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        #header.setSectionResizeMode(0, QHeaderView.Fixed)
        #header.setSectionResizeMode(1, QHeaderView.Stretch)
        #header.setSectionResizeMode(0, QHeaderView.Stretch)
        #header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionsMovable(True)
        header.setStretchLastSection(False)

        # load gui elements and set minimum window dimentions
        self._create_widgets()
        self.setCentralWidget(self.tree)
        self.tree.expandAll()
        # Adding 2pt of padding to the margin to remove horizontal scroll bar and 14pt of padding for the vertical scroll bar
        self.tree.setMinimumWidth(self.tree.columnWidth(0) + self.tree.columnWidth(1) + 2 + 14)
        self.tree.collapseAll()
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setExpanded(True)
        #self._col_one_min_width = self.tree.columnWidth(0)
        #self.tree.sizeHintForIndex(1).
        self.show()

    def close_connections(self):
        print('disconnecting...')
        for (device, feat_name, getattr_partial) in self._slots:
            getattr(device, feat_name + '_changed').connect(getattr_partial)
        # def recursive_func(widget_item):
        #     count = widget_item.childCount()
        #     if count == 0:
        #         #print(widget_item.treeWidget().__repr__())
        #         #import pdb; pdb.set_trace()
        #         print(self.tree.itemWidget(widget_item, 1).__repr__())
        #         self.tree.itemWidget(widget_item, 1).disconnect()
        #         # try:
        #         #     widget_item.treeWidget().disconnect()
        #         # except TypeError:
        #         #     pass
        #     else:
        #         for i in range(count):
        #             recursive_func(widget_item.child(i))
        #
        # tree_root = self.tree.invisibleRootItem()
        # recursive_func(tree_root)

    def _create_widgets(self):
        """Iterate over the available servers and devices, and collect their
        attributes that can be modified by the instrument manager GUI, then
        populate the self.gui and update the GUI"""
        for server_name, server in self.gateway.servers.items():
            server_tree = QTreeWidgetItem(self.tree, [server_name, ''])
            server_tree.setExpanded(True)

            for device_name, device in server.root._devs.items():
                device_tree = QTreeWidgetItem(server_tree, [device_name, ''])
                device_tree.setExpanded(True)

                for feat_name, feat in device._lantz_feats.items():
                    feat_widget = self._generate_feat_widget(feat, feat_name, device)
                    feat_widget.setFont(QFont('Helvetica [Cronyx]', 14))
                    feat_item = QTreeWidgetItem(device_tree, [feat_name, ''])
                    feat_item.sizeHint(0)
                    feat_item.setSizeHint(1, QSize(79,24))
                    self.tree.setItemWidget(feat_item, 1, feat_widget)

                # for dictfeat_name, dictfeat in device._lantz_dictfeats.items():
                #     """Generate a Qt gui element for a lantz dictfeat"""
                #     dictfeat_tree = QTreeWidgetItem(device_tree, [dictfeat_name, ''])
                #     # dummy 'get' of dict feat value in order to force lantz to populate
                #     # its 'subproperties' TODO this is pretty hacky
                #     print(dictfeat_name)
                #     for feat_key in dictfeat.keys:
                #         feat = dictfeat.subproperty(getattr(device, dictfeat_name).instance, feat_key)
                #         feat_widget = self._generate_feat_widget(feat, dictfeat_name, device, dictfeat_key=feat_key)
                #         feat_item = QTreeWidgetItem(dictfeat_tree, ['{} {}'.format(dictfeat_name, feat_key), ''])
                #         self.tree.setItemWidget(feat_item, 1, feat_widget)

                action_tree = QTreeWidgetItem(device_tree, ['Actions', ''])
                for action_name, action in device._lantz_actions.items():
                    ignore_actions = ['initialize', 'finalize', 'update', 'refresh']
                    if action_name in ignore_actions or '_async' in action_name:
                        continue
                    action_widget = self._generate_action_widget(device, action, action_name)
                    action_widget.setFont(QFont('Helvetica [Cronyx]', 14))
                    action_item = QTreeWidgetItem(action_tree, [action_name, ''])
                    self.tree.setItemWidget(action_item, 1, action_widget)


    def _generate_feat_widget(self, feat, feat_name, device, dictfeat_key=None):
        """Generate a Qt gui element for a lantz feat"""
        if dictfeat_key:
            #val = dictfeat.subproperty(getattr(device, feat_name).instance, dictfeat_key)
            val = getattr(device, feat_name)[dictfeat_key] # .__getitem__(dictfeat_key)
        else:
            val = getattr(device, feat_name)
        if feat._config['values']:
            # the lantz feat has only a specific set of allowed values
            # so we make a dropdown box
            widget = QComboBox()
            # print('combo box' + str(widget.sizeHint()))
            # dictionary mapping the possible lantz values to str(values)
            # e.g. {'True' : True, 'False' : False}
            keymapping_dict = {}
            for k in feat._config['values'].keys():
                keymapping_dict[str(k)] = k
            # add the possible values to the dropdown list
            widget.addItems(keymapping_dict.keys())
            widget.setCurrentIndex(list(keymapping_dict.values()).index(val))
            # callback function to modify the GUI when the the feat is changed
            # externally
            # we have to use a partial here because PySignal and RPyC don't
            # place nicely if you .connect() a lambda or other function/method
            # to PySignal
            getattr_func = lambda value, old_value: widget.setCurrentIndex(list(keymapping_dict.values()).index(value))
            # callback function for when the user changes the dropdown selection
            setattr_func = lambda value: setattr(device, feat_name, keymapping_dict[widget.currentText()])
            widget.activated.connect(setattr_func)
        elif isinstance(val, (int, float, Q_)):
            optional_args = {}
            if feat._config['units']:
                optional_args['suffix'] = feat._config['units']
            if feat._config['limits']:
                if len(feat._config['limits']) == 1:
                    # only min or only max was specified e.g.
                    # (,max) or (min,)
                    try:
                        optional_args['min'] = feat._config['limits'][0]
                    except IndexError:
                        optional_args['max'] = feat._config['limits'][1]
                else:
                    # (min, max) was specified
                    optional_args['bounds'] = feat._config['limits']
            # stepping strategy
            optional_args['dec'] = False
            optional_args['minStep'] = 1e-6
            # number of decimal places to display
            optional_args['decimals'] = 6
            optional_args['compactHeight'] = False
            if isinstance(val, int):
                optional_args['int'] = True
                optional_args['minStep'] = 1
                # optional_args['decimals'] = 10
            widget = SpinBox(**optional_args)

            widget.resize(79, 24)
            print(widget.sizeHint())
            def sizeHint(self):
                return QSize(79, 24)
            widget.sizeHint = sizeHint.__get__(widget, SpinBox)
            print(widget.sizeHint())

            #widget.setSizeHint(QSize(120, 20))
            #print(widget.sizeHint())
            if isinstance(val, Q_):
                widget.setValue(val.to(feat._config['units']).m)
            else:
                widget.setValue(val)
            # callback function for when the user changes the feat value
            # from the GUI
            if feat._config['units']:
                setattr_func = lambda value: setattr(device, feat_name, Q_(widget.value(), feat._config['units']))
                def getattr_func(value, old_value):
                    if isinstance(value, Q_):
                        widget.setValue(value.to(feat._config['units']).m)
                    else:
                        widget.setValue(value)
            else:
                setattr_func = lambda value: setattr(device, feat_name, widget.value())
                getattr_func = lambda value, old_value: widget.setValue(value)
            widget.sigValueChanged.connect(setattr_func)
        elif isinstance(val, str):
            widget = QLineEdit()
            widget.setText(val)
            setattr_func = lambda value: setattr(device, feat_name, widget.text())
            widget.textChanged.connect(setattr_func)
            getattr_func = lambda value, old_value: widget.setText(value)
            widget.setReadOnly(feat._config['read_once'])
        else:
            widget = QLineEdit()
            widget.setText(str(feat))
            widget.setReadOnly(feat._config['read_once'])
            getattr_func = lambda value, old_value: widget.setText(value)

        getattr_func.__name__ = 'InstrumentManager_getattr_partial'
        getattr_partial = functools.partial(getattr_func)
        functools.update_wrapper(getattr_partial, getattr_func)
        getattr_partial.__name__ = 'InstrumentManager_getattr_partial'
        getattr(device, feat_name + '_changed').connect(getattr_partial)
        self._slots.append(tuple([device, feat_name, getattr_partial]))
        print(widget.__repr__())
        return widget


    def _generate_action_widget(self, device, action, action_name):
        """Generate a Qt gui element for a lantz action"""
        action_button = QPushButton(action_name, self.tree)
        action_button.setFont(QFont('Helvetica [Cronyx]', 12))

        action_func = lambda: getattr(device, action_name)()
        action_button.clicked.connect(action_func)
        return action_button


if __name__ ==  '__main__':
    import logging
    import time
    import sys
    from PyQt5.QtCore import Qt
    from nspyre.gui.app import NSpyreApp

    # configure server logging behavior
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s -- %(levelname)s -- %(message)s',
                        handlers=[logging.StreamHandler()])

    logging.info('starting Instrument Manager...')
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = NSpyreApp([sys.argv])
    pyqtgraph_connectCleanup()
    with InservGateway() as isg:
        inserv_window = InstrumentManagerWindow(isg)
        app.exec()
        inserv_window.close_connections()
        print('second thing')
        time.sleep(5)
        isg.disconnect_servers()
        time.sleep(5)
    print('exiting')
    #app.disconnect()
    time.sleep(3)
    sys.exit()
