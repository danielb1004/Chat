import re

with open('src/index.css', 'r') as f:
    css = f.read()

# Update CSS variables
css = re.sub(r'--brand: #36c70c;', '--brand: #359946;', css)
css = re.sub(r'--brand-dark: #209600;', '--brand-dark: #216630;', css)
css = re.sub(r'--brand-light: #eaf8e5;', '--brand-light: #eaf3eb;', css)

# Update gradients and other hex greens to the new brand colors
css = re.sub(r'#45dc17', '#42b455', css)
css = re.sub(r'#25aa00', '#359946', css)
css = re.sub(r'#168000', '#216630', css)

css = re.sub(r'#40d414', '#42b455', css)
css = re.sub(r'#2bb300', '#359946', css)
css = re.sub(r'#1f8d00', '#216630', css)

css = re.sub(r'#3acb12', '#42b455', css)
css = re.sub(r'#24a800', '#359946', css)

css = re.sub(r'#3acd13', '#42b455', css)
css = re.sub(r'#1f9700', '#359946', css)

# Update RGBA values
css = re.sub(r'rgba\(54,\s*199,\s*12,\s*', 'rgba(53, 153, 70, ', css)
css = re.sub(r'rgba\(32,\s*150,\s*0,\s*', 'rgba(33, 102, 48, ', css)

with open('src/index.css', 'w') as f:
    f.write(css)

print("Colors updated successfully!")
