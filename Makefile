# ~/Chron-LLM/Makefile

# 物理層 (llama.cpp) へのパス
LLAMA_DIR = ../llama.cpp
OUT_DIR = $(LLAMA_DIR)/build/bin
TARGET = $(OUT_DIR)/libllama_wrapper.so

# コンパイラ設定
CXX = g++
CXXFLAGS = -shared -fPIC -g -O0

# インクルードとリンク設定
INCLUDES = -I$(LLAMA_DIR)/include -I$(LLAMA_DIR)/ggml/include
LDFLAGS = -L$(OUT_DIR) -lllama -Wl,-rpath,'$$ORIGIN'

# ソースファイル
SRCS = src/libllama_wrapper.cpp src/my_llama.c

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SRCS)
	@echo "Building Chron-LLM Immune System Wrapper..."  # ← この行頭のスペースを消して、Tabキーを1回押す
	@mkdir -p $(OUT_DIR)                                 # ← ここもTab
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(SRCS) $(LDFLAGS) -o $(TARGET) # ← ここもTab
	@echo "✨ Build successful: $(TARGET)"               # ← ここもTab

clean:
	@echo "Cleaning up..."                               # ← ここもTab
	rm -f $(TARGET)                                      # ← ここもTab

# cd ~/Chron-LLM
# make