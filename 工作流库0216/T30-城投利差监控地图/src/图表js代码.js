var title=_data?.['title']
var min_value=_data?.['min_value']
var max_value=_data?.['max_value']
var province_stats = _data?.['province_stats']

//_constructorType、_setMapArea、mapData、_Highcharts都为项目中暴露出来的变量
// _constructorType为构造类型
_constructorType = "mapChart";
// _setMapArea用于设置区域：值为"China"或"Global"
_setMapArea("China");
// mapData为地图数据
//如果已获取到地图数据，将上面python代码获取到的数据中所需的值塞进地图数据 
console.log(mapData);
if (mapData) {
  mapData.forEach((el) => {
    const filteredData = _data["省级"].filter(
      (item) => el.name === item.name
    )[0];
    el.drilldown = el.properties["filename"];
    el.value = filteredData?.value;
    el.date = filteredData?.dt;
  });
}
// 地图下钻事件发生，要获取新地图的数据，封装函数，发送请求
const GetDrilldownMapData=async function (url = "") {
  // Default options are marked with *
  const response = await fetch(url, {
    method: "GET",
    mode: "cors"
  });
  return response.json(); 
}
_options = {
  chart: {
    // 图表下钻事件
    events: {
      drilldown: function (e) {
        if (!e.seriesOptions) {
          const chart = this;
          const mapKey = "countries/cn/" + e.point.drilldown + "-all";
          let fail = setTimeout(function () {
            if (!_Highcharts.maps[mapKey]) {
              chart.showLoading(
                '<i class="icon-frown"></i> Failed loading ' + e.point.name
              );
              fail = setTimeout(function () {
                chart.hideLoading();
              }, 1000);
            }
          }, 3000);
          chart.showLoading('<i class="icon-spinner icon-spin icon-3x"></i>'); // Font Awesome spinner
           //调用前面封装的函数发送请求，同样将需要的数据塞进去   
           GetDrilldownMapData("https://geojson.cn/api/china/" + e.point.drilldown + ".json").then(
            function (geojson) {
              mapData = _Highcharts.geojson(geojson);
              console.log(mapData)

              // --- 开始修改 ---
              // 1. 从 province_stats 中查找当前省份的最大最小值
              const current_province_stats = province_stats.filter(p => p.name === e.point.name)[0];
              let province_min = current_province_stats?.min_value;
              let province_max = current_province_stats?.max_value;

              mapData.forEach((el,i)=>{
                const filteredData = _data?.["地级市"].filter(
                      (item) =>  el.name=== item?.['CITY']||el.name.includes(item?.['CITY'])||item?.['CITY']?.includes(el.name)
                    )[0];
                
                el.value=filteredData?.['CLOSE'];
              });

              // 如果没有找到任何有效数据，给一个默认范围
              if (province_min === undefined) province_min = 0;
              if (province_max === undefined) province_max = 0;

              // 2. 更新图表的 colorAxis
              chart.update({
                  colorAxis: {
                      min: province_min,
                      max: province_max,
                  }
              });
              // --- 结束修改 ---

              chart.hideLoading();
              clearTimeout(fail);
              chart.addSeriesAsDrilldown(e.point, {
                name: e.point.name,
                data: mapData,
                dataLabels: {
                  enabled: true,
                  format: "{point.name}",
                },
                tooltip: {
                    pointFormatter: function () {
                      return (
                        this.name+":"+
                        this.value+'BP'
                      );
                    },
                  },
                
              });
            }
          );
        }
        this.setTitle(null, { text: e.point.name });
      },
      drillup: function () {
        // --- 开始修改 ---
        // 恢复全国的 colorAxis
        this.update({
            colorAxis: {
                min: min_value,
                max: max_value,
            }
        });
        // --- 结束修改 ---
        this.setTitle(null, { text: title });
      },
    },
  },
  // 序列
  series: [
    // 地图
    {
      //地图数据
      data: mapData,
      // 曲线名
      name: "China",
      // 数据标签
      dataLabels: {
        enabled: true,
        format: "{point.properties.name}",
      },
      tooltip: {
        pointFormatter: function () {
          return (
            this.name +
            ": " +
            this.value +
            "% <br/> 日期: " +
            new Date(this.date).toLocaleDateString()
          );
        },
      },
    },
  ],
  // 下钻样式
  drilldown: {
    // 有下钻功能的points的dataLabel样式
    activeDataLabelStyle: {
      // dataLabel字体颜色
      color: "#FFFFFF",
      // 文字装饰线
      textDecoration: "none",
      // 文字外框
      textOutline: "1px #000000",
    },
    // 返回按钮
    drillUpButton: {
      relativeTo: "spacingBox",
      position: {
        x: 0,
        y: 60,
      },
    },
  },
  //标题
  title:{
    text:title
  },
  // 图例（颜色轴）
  legend: {
    layout: "vertical",
    align: "right",
    verticalAlign: "middle",
  },
  // 颜色渲染
  colorAxis: {
    min: min_value,
    max: max_value,
    // 最小值颜色
    minColor: "#00FF00",
    // 最大值颜色
    maxColor: "#FF0000",
  },
  // 地图导航栏
  mapNavigation: {
    enabled: true,
    buttonOptions: {
      // 缩放器位置
      verticalAlign: "bottom",
    },
  },
  // 图形选项
  plotOptions: {
    map: {
      states: {
        hover: {
          // 悬浮颜色
          color: "#EEDD66",
        },
      },
    },
  },
};
