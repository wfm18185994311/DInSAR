import os
import esa_snappy
from esa_snappy import ProductIO, GPF, HashMap, jpy

# 获取 Java 类型
Integer = jpy.get_type('java.lang.Integer')
Double = jpy.get_type('java.lang.Double')
String = jpy.get_type('java.lang.String')

# 读取产品
def read_product(product_path):
    try:
        return ProductIO.readProduct(product_path)
    except Exception as e:
        print(f"读取产品时出错: {e}")
        exit(1)

# 应用 Multi-looking
def apply_multilook(product):
    try:
        parameters = HashMap()
        parameters.put('nRgLooks', Integer(4))  # Range方向上的looks数量
        parameters.put('nAzLooks', Integer(1))  # Azimuth方向上的looks数量
        parameters.put('grSquarePixel', True)   # 是否使用正方形像素
        parameters.put('outputIntensity', False) # 是否输出强度信息（如果不需要设置为False）

        return GPF.createProduct('Multilook', parameters, product)
    except Exception as e:
        print(f"应用 Multi-looking 时出错: {e}")
        exit(1)

# 应用 Goldstein Phase Filtering
def apply_goldstein_phase_filtering(product):
    try:
        parameters = HashMap()
        parameters.put('adaptiveFilterExponent', Double(1.0))
        parameters.put('fftSize', Integer(64))
        parameters.put('windowSize', Integer(3))
        parameters.put('coherenceThreshold', Double(0.2))

        return GPF.createProduct('GoldsteinPhaseFiltering', parameters, product)
    except Exception as e:
        print(f"应用 Goldstein Phase Filtering 时出错: {e}")
        exit(1)

# 保存产品
def save_product(product, output_path):
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
        ProductIO.writeProduct(product, output_path, 'BEAM-DIMAP')
    except Exception as e:
        print(f"保存产品时出错: {e}")
        exit(1)

# 主函数 - 处理干涉图产品
def process_multilook(interferogram_product_path, output_path):
    try:
        # 读取干涉图产品
        interferogram_product = read_product(interferogram_product_path)

        # 应用 Multi-looking
        multilooked_product = apply_multilook(interferogram_product)
        multilooked_output_file_path = os.path.join(output_path, os.path.basename(interferogram_product_path).replace('.dim', '_multilook.dim'))
        save_product(multilooked_product, multilooked_output_file_path)
        print(f"Multi-looking 处理完成，结果已保存到 {multilooked_output_file_path}")

        # 应用 Goldstein Phase Filtering
        goldstein_product = apply_goldstein_phase_filtering(multilooked_product)
        goldstein_output_file_path = os.path.join(output_path, os.path.basename(interferogram_product_path).replace('.dim', '_goldstein.dim'))
        save_product(goldstein_product, goldstein_output_file_path)
        print(f"Goldstein Phase Filtering 处理完成，结果已保存到 {goldstein_output_file_path}")

    except Exception as e:
        print(f"处理 Multi-looking 或 Goldstein Phase Filtering 时出错: {e}")
        exit(1)

# 调用示例
if __name__ == "__main__":
    # 输入干涉图产品路径（这个路径是你生成干涉图的结果路径）
    interferogram_product_path = '/data/wangfengmao_file/aipy/output/S1A_IW_SLC__1SDV_20220110T231926_20220110T231953_041405_04EC57_103E_interferogram.dim'

    # 输出路径（保存处理后的Multi-looking和Goldstein Phase Filtering产品）
    output_path = '/data/wangfengmao_file/aipy/output'

    # 运行 Multi-looking 和 Goldstein Phase Filtering 处理
    process_multilook(interferogram_product_path, output_path)
