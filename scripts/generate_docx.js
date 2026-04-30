const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType } = require('docx');
const fs = require('fs');

// Helper function to create a border style
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

// ============ 01_抗炎饮食与营养科普 ============
const doc01 = new Document({
  styles: {
    default: { document: { run: { font: "微软雅黑", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "微软雅黑" },
        paragraph: { spacing: { before: 240, after: 240 } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "微软雅黑" },
        paragraph: { spacing: { before: 180, after: 180 } } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        alignment: AlignmentType.CENTER,
        children: [new TextRun("抗炎饮食与营养科普知识库")]
      }),
      new Paragraph({ children: [new TextRun("整理来源：小红书、微信读书等平台的健康知识截图")] }),
      new Paragraph({ children: [new TextRun("整理时间：2026年3月15日")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 一、坚果的ω-6与ω-3比例指南
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("一、坚果的ω-6与ω-3比例指南")] }),
      new Paragraph({ children: [new TextRun({ text: "来源：注册营养师盼盼", bold: true })] }),
      new Paragraph({ children: [new TextRun("")] }),
      new Paragraph({ children: [new TextRun({ text: "坚持吃（比例优秀）", bold: true })] }),
      new Paragraph({ children: [new TextRun("亚麻籽 0.2:1 | 奇亚籽 1:3 | 核桃 4:1 | 夏威夷果 6.6:1 | 碧根果 21:1")] }),
      new Paragraph({ children: [new TextRun("")] }),
      new Paragraph({ children: [new TextRun({ text: "经常吃（比例良好）", bold: true })] }),
      new Paragraph({ children: [new TextRun("榛子 90:1 | 腰果 125:1 | 开心果 62:1 | 巴旦木 410:1 | 南瓜子 178:1 | 花生 349:1")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 二、抗炎食物ORAC值排行榜
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("二、抗炎食物ORAC值排行榜")] }),
      new Paragraph({ children: [new TextRun({ text: "来源：营养师黑皮", bold: true })] }),
      new Paragraph({ children: [new TextRun("")] }),
      new Paragraph({ children: [new TextRun({ text: "重点推荐：肉桂和姜黄是日常最容易获取的高ORAC值香料！", italics: true })] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 三、21种抗炎最佳食物清单
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("三、21种抗炎最佳食物清单")] }),
      new Paragraph({ children: [new TextRun({ text: "水果类：", bold: true }), new TextRun("余甘子、草莓、石榴、蓝莓、李子")] }),
      new Paragraph({ children: [new TextRun({ text: "谷物与种子：", bold: true }), new TextRun("荞麦、小米、燕麦、藜麦、核桃")] }),
      new Paragraph({ children: [new TextRun({ text: "其他抗炎食物：", bold: true }), new TextRun("咖啡、茶、开心果、黑巧、丁香、薄荷、肉桂、姜黄、紫甘蓝、甜菜、辣椒")] }),
      new Paragraph({ children: [new TextRun({ text: "动物源性：", bold: true }), new TextRun("酸奶、三文鱼、银鳕鱼、鸡蛋")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 四、抗炎膳食宝塔
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("四、抗炎膳食宝塔")] }),
      new Paragraph({ children: [new TextRun({ text: "大量摄入（塔底）：", bold: true }), new TextRun("全谷物、豆类、蔬菜、水果")] }),
      new Paragraph({ children: [new TextRun({ text: "较多摄入：", bold: true }), new TextRun("大豆食品、鱼类贝类、健康脂肪")] }),
      new Paragraph({ children: [new TextRun({ text: "适量摄入：", bold: true }), new TextRun("补充剂、茶、香料、禽肉瘦肉")] }),
      new Paragraph({ children: [new TextRun({ text: "少量摄入（塔尖）：", bold: true }), new TextRun("红酒、健康甜点")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 五、饮食红黑榜
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("五、饮食红黑榜")] }),
      new Paragraph({ children: [new TextRun({ text: "红榜（推荐）：", bold: true }), new TextRun("芹菜、油菜、茼蒿、春笋、银耳、红枣、山药、鲜蚕豆、豆芽、韭菜、紫甘蓝、香椿")] }),
      new Paragraph({ children: [new TextRun({ text: "黑榜（避免）：", bold: true }), new TextRun("鸡肉、螃蟹、羊肉、虾、生冷寒凉、海鱼、酸性食物、辛辣刺激、肥腻、发酵物")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 六、高膳食纤维食物清单（新增）
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("六、高膳食纤维食物清单")] }),
      new Paragraph({ children: [new TextRun({ text: "来源：Rika黄老师", bold: true })] }),
      new Paragraph({ children: [new TextRun("")] }),
      new Paragraph({ children: [new TextRun({ text: "谷物类：", bold: true }), new TextRun("燕麦、荞麦、糙米、玉米、小米")] }),
      new Paragraph({ children: [new TextRun({ text: "豆类：", bold: true }), new TextRun("黄豆、红豆、黑豆、鹰嘴豆、芸豆")] }),
      new Paragraph({ children: [new TextRun({ text: "蔬菜类：", bold: true }), new TextRun("菠菜、西兰花、芹菜、竹笋、南瓜")] }),
      new Paragraph({ children: [new TextRun({ text: "水果类：", bold: true }), new TextRun("苹果、石榴、猕猴桃、火龙果、蓝莓")] }),
      new Paragraph({ children: [new TextRun({ text: "菌藻类：", bold: true }), new TextRun("木耳、香菇、海带、裙带菜、银耳")] }),
      new Paragraph({ children: [new TextRun({ text: "坚果类：", bold: true }), new TextRun("黑芝麻、杏仁、核桃、巴旦木、腰果")] }),
      new Paragraph({ children: [new TextRun("")] }),
      new Paragraph({ children: [new TextRun({ text: "本文档由AI整理生成，仅供参考学习使用", italics: true, size: 20 })] }),
      new Paragraph({ children: [new TextRun({ text: "更新记录：2026年3月18日 - 新增高膳食纤维食物清单", italics: true, size: 20 })] }),
    ]
  }]
});

// ============ 04_日常饮食建议 ============
const doc04 = new Document({
  styles: {
    default: { document: { run: { font: "微软雅黑", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "微软雅黑" },
        paragraph: { spacing: { before: 240, after: 240 } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "微软雅黑" },
        paragraph: { spacing: { before: 180, after: 180 } } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        alignment: AlignmentType.CENTER,
        children: [new TextRun("日常饮食建议与食谱")]
      }),
      new Paragraph({ children: [new TextRun("整理来源：微信视频号、小红书等平台的健康饮食内容")] }),
      new Paragraph({ children: [new TextRun("整理时间：2026年3月15日")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 一、健康早餐建议
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("一、健康早餐建议（以50岁人群为例）")] }),
      new Paragraph({ children: [new TextRun({ text: "推荐搭配：", bold: true })] }),
      new Paragraph({ children: [new TextRun("• 全麦吐司1-2片 + 天然花生酱")] }),
      new Paragraph({ children: [new TextRun("• 煮鸡蛋1个")] }),
      new Paragraph({ children: [new TextRun("• 新鲜浆果（草莓/蓝莓）")] }),
      new Paragraph({ children: [new TextRun("• 酸奶一小杯")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 二、全日食谱推荐
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("二、全日食谱推荐")] }),
      new Paragraph({ children: [new TextRun({ text: "标准成人一日饮食量：", bold: true })] }),
      new Paragraph({ children: [new TextRun("• 粮食200g（粗粮50g）")] }),
      new Paragraph({ children: [new TextRun("• 鸡蛋1个、牛奶1袋")] }),
      new Paragraph({ children: [new TextRun("• 肉类100g、虾仁25g")] }),
      new Paragraph({ children: [new TextRun("• 蔬菜500g、水果200g")] }),
      new Paragraph({ children: [new TextRun("• 北豆腐50g、油20g、盐5g")] }),
      new Paragraph({ children: [new TextRun("")] }),
      new Paragraph({ children: [new TextRun({ text: "营养搭配要点：", bold: true })] }),
      new Paragraph({ children: [new TextRun("粗细搭配、荤素搭配、五色蔬菜、适量水果、少油少盐")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 三、逆转脂肪肝饮食指南（新增）
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("三、逆转脂肪肝饮食指南")] }),
      new Paragraph({ children: [new TextRun({ text: "来源：医路向前巍子", bold: true })] }),
      new Paragraph({ children: [new TextRun("")] }),
      new Paragraph({ children: [new TextRun({ text: "做好这几步，有可能会逆转脂肪肝：", bold: true })] }),
      new Paragraph({ children: [new TextRun("1. 肥胖超重的人减肥")] }),
      new Paragraph({ children: [new TextRun("2. 爱喝酒的人戒酒")] }),
      new Paragraph({ children: [new TextRun("3. 荤素搭配，不一味吃素，补充优质蛋白")] }),
      new Paragraph({ children: [new TextRun("4. 适当吃杂粮")] }),
      new Paragraph({ children: [new TextRun("5. 适当摄入脂肪")] }),
      new Paragraph({ children: [new TextRun("6. 戒掉零食")] }),
      new Paragraph({ children: [new TextRun("7. 补充维生素")] }),
      new Paragraph({ children: [new TextRun("8. 适当的运动")] }),
      new Paragraph({ children: [new TextRun("")] }),
      new Paragraph({ children: [new TextRun({ text: "做好这几点，对脂肪肝逆转有帮助", italics: true })] }),
      new Paragraph({ children: [new TextRun("")] }),
      new Paragraph({ children: [new TextRun({ text: "本文档由AI整理生成，仅供参考学习使用", italics: true, size: 20 })] }),
      new Paragraph({ children: [new TextRun({ text: "更新记录：2026年3月18日 - 新增逆转脂肪肝饮食指南", italics: true, size: 20 })] }),
    ]
  }]
});

// ============ 03_中医养生与食疗 ============
const doc03 = new Document({
  styles: {
    default: { document: { run: { font: "微软雅黑", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "微软雅黑" },
        paragraph: { spacing: { before: 240, after: 240 } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "微软雅黑" },
        paragraph: { spacing: { before: 180, after: 180 } } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        alignment: AlignmentType.CENTER,
        children: [new TextRun("中医养生与食疗知识库")]
      }),
      new Paragraph({ children: [new TextRun("整理来源：微信读书、小红书、豆包等平台的中医养生内容")] }),
      new Paragraph({ children: [new TextRun("整理时间：2026年3月15日")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 一、三伏天养生指南
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("一、三伏天养生指南")] }),
      new Paragraph({ children: [new TextRun({ text: "初伏 - 清内热：", bold: true }), new TextRun("食用苦瓜、丝瓜、冬瓜、黄瓜降火")] }),
      new Paragraph({ children: [new TextRun({ text: "三伏茶配方：", bold: true }), new TextRun("金银花、夏枯草各10g，甘草、菊花、茯苓、麦冬、桑叶各5g，煮20分钟")] }),
      new Paragraph({ children: [new TextRun({ text: "中伏 - 健脾祛湿：", bold: true }), new TextRun("三豆汤（黑豆、赤小豆、绿豆1:1:1）")] }),
      new Paragraph({ children: [new TextRun({ text: "末伏 - 排寒补阳：", bold: true }), new TextRun("黄芪姜枣茶（生姜10g、红枣2个、黄芪5g、枸杞10g）")] }),
      new Paragraph({ children: [new TextRun({ text: "出伏 - 滋阴养血：", bold: true }), new TextRun("枸杞、桑葚、麦冬煮水（1:1:1）")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 二、仲冬养生食疗方
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("二、仲冬养生食疗方")] }),
      new Paragraph({ children: [new TextRun({ text: "仲冬，五脏要同补，重点是大补心和肾", bold: true })] }),
      new Paragraph({ children: [new TextRun({ text: "补肾养心食疗方：", bold: true }), new TextRun("栗子6个、核桃6个、莲子6个、枸杞1把、葡萄干1把、陈皮1/4~1/2")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 三、经络穴位知识
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("三、经络穴位知识")] }),
      new Paragraph({ children: [new TextRun({ text: "厥阴俞穴位置：", bold: true }), new TextRun("第4胸椎棘突下旁开1.5寸处")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 四、中药五味理论
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("四、中药五味理论")] }),
      new Paragraph({ children: [new TextRun({ text: "来源：朱氏非遗话中医第十五课", bold: true })] }),
      new Paragraph({ children: [new TextRun("酸（收敛）：山茱萸、五味子、五倍子、乌梅")] }),
      new Paragraph({ children: [new TextRun("苦（泄、燥、坚）：大黄、黄连")] }),
      new Paragraph({ children: [new TextRun("甘（补、缓、和）：人参、饴糖、甘草")] }),
      new Paragraph({ children: [new TextRun("辛（散、行）：麻黄、薄荷、木香、红花")] }),
      new Paragraph({ children: [new TextRun("咸（软、下）：海藻、昆布、鳖甲、芒硝")] }),
      new Paragraph({ children: [new TextRun("淡（渗、利）：猪苓、茯苓、薏苡仁、通草")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 五、传统中药方剂
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("五、传统中药方剂")] }),
      new Paragraph({ children: [new TextRun({ text: "龙化丹：", bold: true }), new TextRun("治疗小儿耳后湿疹，配方含炉甘石")] }),
      new Paragraph({ children: [new TextRun({ text: "虎潜丸（健步强身丸）：", bold: true }), new TextRun("专调两腿酸软、腰腿痛、关节痛")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 六、柿子养生功效
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("六、柿子养生功效")] }),
      new Paragraph({ children: [new TextRun({ text: "来源：一柿顶十药", bold: true })] }),
      new Paragraph({ children: [new TextRun({ text: "青柿：", bold: true }), new TextRun("去火功效，应对秋燥上火")] }),
      new Paragraph({ children: [new TextRun({ text: "柿饼：", bold: true }), new TextRun("性平甘涩，归心、肺、大肠经")] }),
      new Paragraph({ children: [new TextRun({ text: "柿霜：", bold: true }), new TextRun("清热生津、润泽止咳，治口腔溃疡")] }),
      new Paragraph({ children: [new TextRun({ text: "柿核：", bold: true }), new TextRun("降逆下气，治呃逆（打嗝）")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 七、紫苏生姜红枣水
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("七、紫苏生姜红枣水")] }),
      new Paragraph({ children: [new TextRun({ text: "来源：止水养生日记", bold: true })] }),
      new Paragraph({ children: [new TextRun({ text: "功效：", bold: true }), new TextRun("驱寒暖胃、补益气血")] }),
      new Paragraph({ children: [new TextRun({ text: "适合人群：", bold: true }), new TextRun("容易感冒、手脚胃部不适、受凉后腹泻者")] }),
      new Paragraph({ children: [new TextRun({ text: "做法：", bold: true }), new TextRun("紫苏叶8-10片、生姜3-4片、红枣4-5颗，加水500ml煮沸后小火煮5-10分钟")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 八、醪糟养生
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("八、醪糟养生")] }),
      new Paragraph({ children: [new TextRun({ text: "来源：酒窝姐爱养生", bold: true })] }),
      new Paragraph({ children: [new TextRun({ text: "选购要点：", bold: true }), new TextRun("选配料表干净的醪糟（净化水、糯米、甜酒曲）")] }),
      new Paragraph({ children: [new TextRun({ text: "功效：", bold: true }), new TextRun("醪糟煮蛋，食养气血，巨养颜")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 九、紫苏陈皮水（新增）
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("九、紫苏陈皮水")] }),
      new Paragraph({ children: [new TextRun({ text: "来源：止水养生日记", bold: true })] }),
      new Paragraph({ children: [new TextRun({ text: "功效：", bold: true }), new TextRun("理气健脾、燥湿化痰")] }),
      new Paragraph({ children: [new TextRun({ text: "适合人群：", bold: true }), new TextRun("立秋后湿气仍重，感觉食欲不振、脘腹胀满、咳嗽痰多者")] }),
      new Paragraph({ children: [new TextRun({ text: "搭配原理：", bold: true }), new TextRun("陈皮能理气健脾，燥湿化痰；与紫苏搭配，增强行气宽中、化解脾胃湿浊的功效")] }),
      new Paragraph({ children: [new TextRun({ text: "做法：", bold: true }), new TextRun("紫苏叶8片、陈皮5克，开水冲泡焖5分钟，再放入紫苏叶焖3分钟")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 十、大雪后15天养生指南（新增）
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("十、大雪后15天养生指南")] }),
      new Paragraph({ children: [new TextRun({ text: "来源：懒妈的养生账本", bold: true })] }),
      new Paragraph({ children: [new TextRun({ text: "养生要点：", bold: true }), new TextRun("大雪后15天，就一个字：藏")] }),
      new Paragraph({ children: [new TextRun({ text: "食养原则：", bold: true }), new TextRun("藏精于黑咸，温润滋肾")] }),
      new Paragraph({ children: [new TextRun({ text: "推荐食材：", bold: true }), new TextRun("海带、紫菜、牡蛎、黑豆、黑芝麻、木耳")] }),
      new Paragraph({ children: [new TextRun({ text: "藏暖粥：", bold: true }), new TextRun("黑米、核桃、山药、枸杞同煮，早晚温食")] }),
      new Paragraph({ children: [new TextRun({ text: "地域饮食：", bold: true }), new TextRun("南方莲藕炖排骨，北方小米羊肉粥")] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      // 十一、冬至养生羊肉汤（新增）
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("十一、冬至养生羊肉汤")] }),
      new Paragraph({ children: [new TextRun({ text: "来源：微信读书《顺时生活》", bold: true })] }),
      new Paragraph({ children: [new TextRun({ text: "原料：", bold: true }), new TextRun("羊肉1-2斤、黄芪100克、当归20克、甘蔗2-4节、带皮生姜2块、大枣8个")] }),
      new Paragraph({ children: [new TextRun({ text: "调料：", bold: true }), new TextRun("黄酒1两")] }),
      new Paragraph({ children: [new TextRun({ text: "善养生者，必养冬至", italics: true })] }),
      new Paragraph({ children: [new TextRun("")] }),
      
      new Paragraph({ children: [new TextRun({ text: "本文档由AI整理生成，内容源自各平台中医养生知识", italics: true, size: 20 })] }),
      new Paragraph({ children: [new TextRun({ text: "仅供参考学习使用，如有不适请前往正规医院就诊", italics: true, size: 20 })] }),
      new Paragraph({ children: [new TextRun({ text: "更新记录：2026年3月18日 - 新增紫苏陈皮水、大雪养生、冬至羊肉汤", italics: true, size: 20 })] }),
    ]
  }]
});

// Generate all documents
async function generateDocs() {
  const buffer01 = await Packer.toBuffer(doc01);
  fs.writeFileSync("D:\\新建文件夹\\处理结果\\01_抗炎饮食与营养科普.docx", buffer01);
  console.log("✅ 01_抗炎饮食与营养科普.docx 生成完成");
  
  const buffer04 = await Packer.toBuffer(doc04);
  fs.writeFileSync("D:\\新建文件夹\\处理结果\\04_日常饮食建议.docx", buffer04);
  console.log("✅ 04_日常饮食建议.docx 生成完成");
  
  const buffer03 = await Packer.toBuffer(doc03);
  fs.writeFileSync("D:\\新建文件夹\\处理结果\\03_中医养生与食疗.docx", buffer03);
  console.log("✅ 03_中医养生与食疗.docx 生成完成");
  
  console.log("\n🎉 所有Word文档生成完成！");
}

generateDocs().catch(console.error);
