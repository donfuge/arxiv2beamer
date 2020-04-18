# -*- coding: utf-8 -*-
"""
Created on Sat Apr 18 11:23:35 2020

@author: fuge
"""

from jinja2 import Environment, FileSystemLoader
import os 
from datetime import date
from TexSoup import TexSoup
from TexSoup.data import RArg
import shutil
from  urllib.request import urlopen
import tarfile

#%%
class Figure:
  
  def __init__(self,filename, sectionname="", heightfactor=1, formulas = []):
    self.filename = filename
    self.sectionname = sectionname
    self.formulas = formulas
    self.heightfactor = str(heightfactor)
    
  def __repr__(self):
    return 'Figure filename: ' + self.filename + ', sectionname: ' + self.sectionname + "formulas: " + len(self.formulas) 

#%%
template_dir = "templates" 
figure_template = "beamer_template.txt"

talk = {'author_name': 'Your Name',
        'author_institute': 'Your Institute',
        'shorttitle': 'Short title',
        'title': 'title',
        'date': date.today().strftime("%Y-%m-%d")}
#%%

input_dir = "input"
beamer_fname = "beamer.tex"
source_url = "https://arxiv.org/e-print/1701.03433"
timeout_secs = 10

basename = source_url.split("/")[-1]
#%%
source_dir = os.path.join(input_dir,basename)
source_fname = basename + ".tar.gz"

if not os.path.exists(input_dir): os.makedirs(input_dir)
if not os.path.exists(source_dir): os.makedirs(source_dir)
#%%

if not os.path.exists( os.path.join(source_dir,source_fname)): 

  print("Downloading source...")
  req = urlopen(source_url, None, timeout_secs)
  
  with open(os.path.join(source_dir,source_fname), 'wb') as fp:
    shutil.copyfileobj(req, fp)
    
  print(source_fname + " downloaded")
else:
  print("Source file exists")
#%%
print("Extracting " + source_fname)

with tarfile.open(os.path.join(source_dir,source_fname)) as f:
    f.extractall(source_dir)
#%%
items = os.listdir(source_dir)

tex_files = []
for name in items:
    if name.endswith(".tex"):
      if not name == beamer_fname:
        tex_files.append(name)

if len(tex_files)==1:
  main_tex = tex_files[0]
  print("Latex file found: " + main_tex)
else: 
  print("Multiple tex files...")
  print(tex_files)

  
with open(os.path.join(source_dir,main_tex), "r") as f:
    
  contents = f.read()

  print("Processing Latex file")
  latex_soup = TexSoup(contents)
#%% taking care of packages
packages = latex_soup.find_all('usepackage')

package_string = ""
for package in packages:
  package_string += repr(package)  + "\n"
  
# print(package_string)
#%% taking care of new commands
new_commands = latex_soup.find_all('newcommand')

new_commands_string = ""
for command in new_commands:
  new_commands_string += repr(command)  + "\n"
  
# print(new_commands_string)
#%%
doc = latex_soup.find('document')

current_section = ""
figures = []
formula_cache = []

for node in doc.children:
  # print(node.name)
  if hasattr(node.name,'text'):
    if (node.name.text) == "section":
      current_section = node.string
      # print("Section found:" + current_section)

    elif "figure" in node.name.text:
      
      include_graphics = node.find('includegraphics')
      
      if include_graphics is not None:
        for figarg in include_graphics.args:
          if type(figarg) is RArg:
            # print("Figure found:" + str(figarg.contents[0]))
            figures.append(Figure(filename=str(figarg.contents[0]),sectionname=current_section,formulas=formula_cache))
    
            formula_cache = []
  elif "$" == node.name: 
    # print(node.name)
    formula_cache.append(node.string)
    
# print(figures)
#%%


# http://eosrei.net/articles/2015/11/latex-templates-python-and-jinja2-generate-pdfs

latex_jinja_env = Environment(
	block_start_string = '\BLOCK{',
	block_end_string = '}',
	variable_start_string = '\VAR{',
	variable_end_string = '}',
	comment_start_string = '\#{',
	comment_end_string = '}',
	line_statement_prefix = '%%',
	line_comment_prefix = '%#',
	trim_blocks = True,
	autoescape = False,
	loader = FileSystemLoader(template_dir)
)


template = latex_jinja_env.get_template(figure_template)

output = template.render(package_string = package_string,
                         new_commands_string = new_commands_string,
                         figures = figures, talk = talk)


with open(os.path.join(source_dir,beamer_fname), 'w') as f:
    f.write(output)
print(beamer_fname + " written")
