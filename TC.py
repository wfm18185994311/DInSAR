import os
import esa_snappy
from esa_snappy import ProductIO, GPF, HashMap, jpy

# 确保GPF初始化
GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

# 获取 Java 类型
Integer = jpy.get_type('java.lang.Integer')
Double = jpy.get_type('java.lang.Double')
String = jpy.get_type('java.lang.String')
Boolean = jpy.get_type('java.lang.Boolean')
# 读取产品
def read_product(product_path):
    try:
        return ProductIO.readProduct(product_path)
    except Exception as e:
        print(f"读取产品时出错: {e}")
        exit(1)

# 应用 Phase to Displacement
def apply_phase_to_displacement(product, dem_path):
    try:
        parameters = HashMap()
        parameters.put('wavelength', Double(0.056))  # S1的波长大约是5.6厘米
        parameters.put('referenceDEM', dem_path)  # 使用指定的 DEM 路径
        parameters.put('demName', 'SRTM 3Sec')
        parameters.put('demResamplingMethod', 'BILINEAR_INTERPOLATION')
        parameters.put('pixelSpacingInMeter', Double(10))
        parameters.put('outputType', 'Displacement')
        return GPF.createProduct('PhaseToDisplacement', parameters, product)
    except Exception as e:
        print(f"应用 Phase to Displacement 时出错: {e}")
        exit(1)

# 应用 Range Doppler Terrain Correction
def apply_rd_terrain_correction(product, dem_path):
    try:
        parameters = HashMap()
        parameters.put('demName', 'External DEM')
        parameters.put('externalDEMFile', dem_path)  # 使用指定的 DEM 路径
        parameters.put('externalDEMNoDataValue', Double(0.0))
        parameters.put('demResamplingMethod', 'BILINEAR_INTERPOLATION')
        parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
        parameters.put('pixelSpacingInMeter', Double(10))
        parameters.put('mapProjection', 'AUTO:42001')  # 对应 WGS84(DD)
        parameters.put('maskOutAreaWithoutElevation', Boolean(True))
        parameters.put('outputComplex', Boolean(False))
        return GPF.createProduct('Terrain-Correction', parameters, product)
    except Exception as e:
        print(f"应用 Range Doppler Terrain Correction 时出错: {e}")
        exit(1)

# 保存产品
def save_product(product, output_path):
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
        # 确保输出路径存在
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        ProductIO.writeProduct(product, output_path, 'BEAM-DIMAP')
    except Exception as e:
        print(f"保存产品时出错: {e}")
        exit(1)

# 主函数 - 处理产品
def process_phase_to_displacement_and_terrain_correction(product_path, output_path, dem_path):
    try:
        # 读取产品
        product = read_product(product_path)

        # 应用 Phase to Displacement
        displacement_product = apply_phase_to_displacement(product, dem_path)

        # 应用 Range Doppler Terrain Correction
        rd_corrected_product = apply_rd_terrain_correction(displacement_product, dem_path)

        # 保存结果
        displacement_output_file_path = os.path.join(output_path, os.path.basename(product_path).replace('.dim', '_displacement_terrain_corr.dim'))
        save_product(rd_corrected_product, displacement_output_file_path)
        print(f"Phase to Displacement 和 Range Doppler Terrain Correction 处理完成，结果已保存到 {displacement_output_file_path}")
    except Exception as e:
        print(f"处理 Phase to Displacement 和 Range Doppler Terrain Correction 时出错: {e}")
        exit(1)

# 调用示例
if __name__ == "__main__":
    # 输入产品路径
    product_path = '/data/wangfengmao_file/aipy/output/S1A_IW_SLC__1SDV_20220110T231926_20220110T231953_041405_04EC57_103E_Orb_Stack_Deb_Ifg_ML_Flt_GPF_Unwrapping.dim'
    # 输出路径
    output_path = '/data/wangfengmao_file/aipy/output'
    # DEM 文件路径
    dem_path = '/data/wangfengmao_file/aipy/dem/utm_srtm_57_05.tif'

    # 运行 Phase to Displacement 和 RD Terrain Correction 处理
    process_phase_to_displacement_and_terrain_correction(product_path, output_path, dem_path)
