# coding:utf-8
"""
  Time : 2021/2/2 下午7:57
  Author : vincent
  FileName: generate_code
  Software: PyCharm
  Last Modified by: vincent
  Last Modified time: 2021/2/2 下午7:57
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import math, string

font_path = 'static/fonts/ARIAL.TTF'  # 字体的位置，不同版本的系统会有不同
# font_path = '/Library/Fonts/Hanzipen.ttc'
number = 4  # 生成验证码的位数
size = (70, 25)  # 生成验证码图片的高度和宽度
bgcolor = '#BFBFBF'  # 背景颜色，默认为白色
fontcolor = '#FFFFFF'  # 字体颜色，默认为蓝色
linecolor = (255, 0, 0)  # 干扰线颜色。默认为红色
draw_line = False  # 是否要加入干扰线
line_number = (1, 5)  # 加入干扰线条数的上下限


def get_text():
    """
    生成验证码
    :return:
    """
    source_code = list(string.ascii_uppercase)
    num = list(map(str, string.digits))
    source_code.extend(num)
    return ''.join(random.sample(source_code, number))  # number是生成验证码的位数


def gene_line(draw, width, height):
    """
    绘制干扰线
    :param draw:
    :param width:
    :param height:
    :return:
    """
    begin = (random.randint(0, width), random.randint(0, height))
    end = (random.randint(0, width), random.randint(0, height))
    draw.line([begin, end], fill=linecolor)


def gene_code(save_path='', filename=''):
    width, height = size  # 宽和高
    image = Image.new('RGBA', (width, height), bgcolor)  # 创建图片
    font = ImageFont.truetype(font_path, 20)  # 验证码的字体和字体大小
    # font = ImageFont.truetype(25)                         # 验证码的字体和字体大小
    draw = ImageDraw.Draw(image)  # 创建画笔
    text = get_text()  # 生成字符串
    # print(text)
    font_width, font_height = font.getsize(text)
    # print('font_width:', font_width)
    # print('font_height:', font_height)
    draw.text(((width - font_width) / number + 6, (height - font_height) / number),
              text, font=font, fill=fontcolor)  # 填充字符串
    # draw.text((0, 0),text, font = font, fill = fontcolor)  # 填充字符串
    if draw_line:
        gene_line(draw, width, height)
        gene_line(draw, width, height)
        gene_line(draw, width, height)
        gene_line(draw, width, height)
    # print(image.size)
    # image = image.transform((width + 20, height + 10), Image.AFFINE, (1, -0.3, 0, -0.1, 1, 0), Image.BILINEAR)  # 创建扭曲
    # image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)     # 滤镜，边界加强
    if save_path and filename:
        """如果传入保存路径和文件名，则将验证码图片保存为文件"""
        image.save('%s/%s.png' % (save_path, filename))  # 保存验证码图片
        print("savepath:", save_path)
        return text
    else:
        """如果不传入文件路径和文件名，则将验证码图片对象直接返回"""
        return image, text


if __name__ == "__main__":
    gene_code('.', '1')
