from more_termcolor import colors, colored
from more_termcolor.colors import bold, brightgreen, yellow

bold_text = colored('text', 'yellow')
black = colors.blue('123')
fancy = colors.brightblack(f'this whole string {black} including this {bold_text} fghjfgj')
print(colors.brightyellow('asdfas'))

print(fancy)