🌟 Research TA Agent（研究助教代理）

一个轻量级、本地优先（local-first） 的 AI 学习助手，能够：

📚 搜索你的教材/PDF 并精确标注页码 —
当你把自己的课程资料（教材、课件、论文）放入知识库后，系统会自动检索并返回包含答案的具体段落与页码位置。
与直接使用LLM不同，它会严格依据教授授课时的内容给出答案，不会发散、不跑题、不编造额外解释。
非常适合 做作业、期末复习、写论文 时需要精准、可追溯来源的解读（而且非常容易使用）。

# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp config/.env.example config/.env
# 编辑 .env 文件，填入 OPENAI_API_KEY

# 添加你的教材、课件和数据
cp your_pdfs/*.pdf knowledge_base/
cp your_data/*.csv data/

# 构建检索索引
python build_index.py

# 启动图形界面
streamlit run app.py
