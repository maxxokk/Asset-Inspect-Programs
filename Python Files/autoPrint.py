import pyautogui
import time

num = 13

singles = [-1]

time.sleep(3)

for i in range(num):
    pyautogui.hotkey('ctrl', 'p')

    if i in singles:
        pyautogui.press('enter')
        pyautogui.hotkey('ctrl', 'tab')
        continue

    for x in range(7):
        pyautogui.press('tab')
        time.sleep(0.1)
    pyautogui.press('enter')
    pyautogui.press('down')
    pyautogui.press('tab')

    for y in range(4):
        pyautogui.press('tab')
        time.sleep(0.1)
    pyautogui.press('enter')

    pyautogui.hotkey('ctrl', 'tab')