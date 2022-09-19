"""Widget that generates a simple GUI that allows the user to enter a set of parameters.

Copyright (c) 2021 Jacob Feder
All rights reserved.

This work is licensed under the terms of the 3-Clause BSD license.
For a copy, see <https://opensource.org/licenses/BSD-3-Clause>.
"""
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from pyqtgraph import SpinBox


class ParamsWidget(QWidget):
    """Create a simple GUI widget containing a list of parameters.

    Typical usage example:

    .. code-block:: python

        self.params_widget = ParamsWidget({
                            'pulse_power': {'suffix': 'V', 'siPrefix': True},
                            'pulse_length': {'suffix': 's', 'siPrefix': True},
                            })

        def doSomething(self):
            print(f'Making a pulse with power = {self.params_widget.pulse_power} V, length = {self.params_widget.pulse_length} V'

    """

    def __init__(self, params: dict, *args, **kwargs):
        """Initialize params widget.

        Args:
            params: dictionary mapping parameter names to options, which are 
                    passed as arguments to their corresponding pyqtgraph 
                    spinbox, or to strings. The spinbox options are documented 
                    at https://pyqtgraph.readthedocs.io/en/latest/widgets/spinbox.html. 
                    Additional configuration parameters than be passed are:
                        - display_text: parameter text label
        """
        super().__init__(*args, **kwargs)
        self.params = params
        self.spinboxes = {}
        self.textboxes = {}

        # vertical layout
        total_layout = QVBoxLayout()

        # add parameter spinbox widgets to the layout
        for p in self.params:
            # small layout containing a label and spinbox
            label_param_layout = QHBoxLayout()
            # create parameter label
            label = QLabel()
            try:
                display_text = self.params[p].pop('display_text')
            except KeyError:
                label.setText(p) 
            else:
                label.setText(display_text)
            label_param_layout.addWidget(label)
            if isinstance(self.params[p], str):
                # create textbox (QLineEdit widget)
                textbox = QLineEdit(self.params[p])
                # store the textboxes
                self.textboxes[p] = textbox
                label_param_layout.addWidget(textbox)
            else:
                # create spinbox
                spinbox = SpinBox(**self.params[p])
                # store the spinboxes
                self.spinboxes[p] = spinbox
                label_param_layout.addWidget(spinbox)
            total_layout.addLayout(label_param_layout)

        # add stretch element to take up any extra space below the spinboxes
        total_layout.addStretch()

        self.setLayout(total_layout)

    def all_params(self):
        """Return the current value of all user parameters as a dictionary."""
        all_params = {}
        for p in self.params:
            if isinstance(self.params[p], str):
                all_params[p] = self.textboxes[p].text()
            else:
                all_params[p] = self.spinboxes[p].value()
        return all_params

    def __getattr__(self, attr: str):
        """Allow easy access to the parameter values."""
        if attr in self.params:
            if isinstance(self.params[attr], str):
                return self.textboxes[attr].text()
            else:
                return self.spinboxes[attr].value()
        else:
            # raise the default python error when an attribute isn't found
            return self.__getattribute__(attr)
