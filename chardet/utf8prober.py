######################## BEGIN LICENSE BLOCK ########################
# The Original Code is mozilla.org code.
#
# The Initial Developer of the Original Code is
# Netscape Communications Corporation.
# Portions created by the Initial Developer are Copyright (C) 1998
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Mark Pilgrim - port to Python
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301  USA
######################### END LICENSE BLOCK #########################

from .charsetprober import CharSetProber
from .enums import ProbingState, MachineState
from .codingstatemachine import CodingStateMachine
from .mbcssm import UTF8_SM_MODEL



class UTF8Prober(CharSetProber):
    ONE_CHAR_PROB = 0.5

    def __init__(self):
        super(UTF8Prober, self).__init__()
        self.coding_sm = CodingStateMachine(UTF8_SM_MODEL)
        self._num_mb_chars = None
        self.reset()

    def reset(self):
        super(UTF8Prober, self).reset()
        self.coding_sm.reset()
        self._num_mb_chars = 0

    @property
    def charset_name(self):
        return "utf-8"

    def feed(self, byte_str):
        # Don't bother detecting any more if we already found an error
        if self.state != ProbingState.not_me:
            for c in byte_str:
                coding_state = self.coding_sm.next_state(c)
                if coding_state == MachineState.its_me:
                    self._state = ProbingState.found_it
                    break
                elif coding_state == MachineState.start:
                    if self.coding_sm.get_current_charlen() >= 2:
                        self._num_mb_chars += 1
                elif coding_state == MachineState.error:
                    self._state = ProbingState.not_me
                    break

            if self.state == ProbingState.detecting:
                if self.get_confidence() > self.SHORTCUT_THRESHOLD:
                    self._state = ProbingState.found_it

        return self.state

    def get_confidence(self):
        # Make it very unlikely that UTF8 gets chosen if we reached error state
        if self.state == ProbingState.not_me:
            return 0.001
        unlike = 0.99
        if self._num_mb_chars < 6:
            unlike *= self.ONE_CHAR_PROB ** self._num_mb_chars
            return 1.0 - unlike
        else:
            return unlike
