#include <math.h>
#include "llama.h"

// トークンの確率（確信度）を取得する関数
float get_token_prob(struct llama_context * ctx, int token_id) {
    const float * logits = llama_get_logits(ctx);
    const struct llama_model * model = llama_get_model(ctx);
    const struct llama_vocab * vocab = llama_model_get_vocab(model);
    int n_vocab = llama_vocab_n_tokens(vocab);

    // Softmaxのオーバーフロー対策 (Max Logitの計算)
    float max_logit = logits[0];
    for (int i = 1; i < n_vocab; i++) {
        if (logits[i] > max_logit) max_logit = logits[i];
    }

    // 指数和の計算
    double sum = 0.0;
    for (int i = 0; i < n_vocab; i++) {
        sum += expf(logits[i] - max_logit);
    }

    // 指定された token_id の確率を返す
    return expf(logits[token_id] - max_logit) / (float)sum;
}

// 次のトークン予測時のエントロピー（迷いの大きさ）を取得する関数
float get_entropy(struct llama_context * ctx) {
    const float * logits = llama_get_logits(ctx);
    const struct llama_model * model = llama_get_model(ctx);
    const struct llama_vocab * vocab = llama_model_get_vocab(model);
    int n_vocab = llama_vocab_n_tokens(vocab);

    float max_logit = logits[0];
    for (int i = 1; i < n_vocab; i++) {
        if (logits[i] > max_logit) max_logit = logits[i];
    }

    double sum = 0.0;
    for (int i = 0; i < n_vocab; i++) {
        sum += expf(logits[i] - max_logit);
    }

    // エントロピー計算: -Σ(p * log(p))
    double entropy = 0.0;
    for (int i = 0; i < n_vocab; i++) {
        float p = expf(logits[i] - max_logit) / (float)sum;
        if (p > 0.0f) { // log(0) 回避
            entropy -= p * logf(p);
        }
    }
    
    return (float)entropy;
}

/*
cd ~/Chron-LLM

g++ -shared -fPIC -g -O0 \
    -I ~/llama.cpp/include \
    -I ~/llama.cpp/ggml/include \
    src/libllama_wrapper.cpp src/my_llama.c \
    -L ~/llama.cpp/build/bin \
    -lllama \
    -Wl,-rpath,'$ORIGIN' \
    -o ~/llama.cpp/build/bin/libllama_wrapper.so
*/