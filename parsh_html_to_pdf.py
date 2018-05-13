import os
import requests
from bs4 import BeautifulSoup
import pdfkit
from PyPDF2 import PdfFileReader, PdfFileWriter

# Get the chapter content
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
</head>
<body>
{content}
</body>
</html>
"""
def get_one_page(url):
    response= requests.get(url)
    if response.status_code == 200:
        return response.content.decode("utf8","ignore").encode("gbk","ignore")

def get_content(url):
    """
    parse the URL，get the content in the html
    :param url: target url
    :return: html
    """
    html = get_one_page(url)
    soup = BeautifulSoup(html, 'html.parser')
    content =soup.find('div', attrs={'itemprop': 'articleBody'})
    html = html_template.format(content=content)
    return html

# Get the chapter names
def parse_title_and_url(html):
    """
    解析全部章节的标题和url
    :param html: 需要解析的网页内容
    :return None
    """
    soup = BeautifulSoup(html, 'html.parser')
    # Get the book name
    book_name = soup.find('div', class_='wy-side-nav-search').a.text
    menu = soup.find_all('div', class_='section')
    chapters = menu[0].div.ul.find_all('li', class_='toctree-l1')
    for chapter in chapters:
        info = {}
        # Get the first lever chapter name and url
        # If there are '/' and '*' in the chapter name, it would save name false
        info['title'] = chapter.a.text.replace('/', '').replace('*', '')
        info['url'] = base_url + chapter.a.get('href')
        info['child_chapters'] = []

        # Get the second lever chapter name and url
        if chapter.ul is not None:
            child_chapters = chapter.ul.find_all('li')
            for child in child_chapters:
                url = child.a.get('href')
                # 如果在url中存在'#'，则此url为页面内链接，不会跳转到其他页面
                # 所以不需要保存
                if '#' not in url:
                    info['child_chapters'].append({
                        'title': child.a.text.replace('/', '').replace('*', ''),
                        'url': base_url + child.a.get('href')})

        chapter_info.append(info)


# Save pdf
def save_pdf(html, filename):
    """
     save all the documents in pdf
    :param html:  html content
    :param file_name: pdf file_name
    :return:
    """
    options = {
        'page-size': 'Letter',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'custom-header': [
            ('Accept-Encoding', 'gzip')
        ],
        'cookie': [
            ('cookie-name1', 'cookie-value1'),
            ('cookie-name2', 'cookie-value2'),
        ],
        'outline-depth': 10}
    pdfkit.from_string(html, filename, options=options)

def parse_html_to_pdf():
    """
    parse URL，get html，save as pdf
    :return: None
    """
    try:
        for chapter in chapter_info:
            ctitle = chapter['title']
            url = chapter['url']
            # make directories(multi-dir)            
            dir_name = os.path.join(os.path.dirname(__file__), 'gen', ctitle)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)

            html = get_content(url)

            pdf_path = os.path.join(dir_name, ctitle + '.pdf')
            save_pdf(html, os.path.join(dir_name, ctitle + '.pdf'))

            children = chapter['child_chapters']
            if children:
                for child in children:
                    html = get_content(child['url'])
                    pdf_path = os.path.join(dir_name, child['title'] + '.pdf')
                    save_pdf(html, pdf_path)
    except Exception as e:
        print(e)
        
# Merge pdf documents 
def merge_pdf(infnList, outfn):
    """
    合并pdf
    :param infnList: 要合并的PDF文件路径列表
    :param outfn: 保存的PDF文件名
    :return: None
    """
    page_num = 0
    pdf_output = PdfFileWriter()

    for pdf in infnList:
        # Merge the first_dir content
        first_level_title = pdf['title']
        dir_name = os.path.join(os.path.dirname(__file__), 'gen', first_level_title)
        pdf_path = os.path.join(dir_name, first_level_title + '.pdf')

        pdf_input = PdfFileReader(open(pdf_path, 'rb'))
        # Get the total_num pdf
        page_count = pdf_input.getNumPages()
        for i in range(page_count):
            pdf_output.addPage(pdf_input.getPage(i))

        # Add bookmark

        parent_bookmark = pdf_output.addBookmark(first_level_title, pagenum=page_num)

        # Page increase
        page_num += page_count

        # Merge the sub_chapter
        if pdf['child_chapters']:
            for child in pdf['child_chapters']:
                second_level_title = child['title']
                pdf_path = os.path.join(dir_name, second_level_title + '.pdf')

                pdf_input = PdfFileReader(open(pdf_path, 'rb'))
                # Get the total_num pdf
                page_count = pdf_input.getNumPages()
                for i in range(page_count):
                    pdf_output.addPage(pdf_input.getPage(i))

                # Add bookmark
                pdf_output.addBookmark(second_level_title, pagenum=page_num, parent=parent_bookmark)

                # Page increase
                page_num += page_count
    # Merge all the pdf
    pdf_output.write(open(outfn, 'wb'))

    

# Global variables
base_url = 'http://python3-cookbook.readthedocs.io/zh_CN/latest/'
 
chapter_info = []
html = get_one_page(base_url)
html_content = get_content(base_url)

parse_title_and_url(html)
parse_html_to_pdf()
save_pdf(html_content, 'python3_cookbook.pdf')

merge_pdf(chapter_info, 'merge_gen')



        
