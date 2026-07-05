#include "llama.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern "C"
{

    /* ---------------------------------------------------------
       モデルロードラッパ
       --------------------------------------------------------- */
    struct llama_model *my_llama_model_load(const char *path)
    {
        char *local_path = strdup(path);
        struct llama_model_params params = llama_model_default_params();
        struct llama_model *model = llama_model_load_from_file(local_path, params);
        free(local_path);
        return model;
    }

    /* ---------------------------------------------------------
       コンテキスト初期化ラッパ
       --------------------------------------------------------- */
    struct llama_context *my_llama_init(struct llama_model *model, int32_t n_ctx)
    {
        struct llama_context_params params = llama_context_default_params();
        if (n_ctx > 0)
        {
            params.n_ctx = n_ctx;
        }
        return llama_init_from_model(model, params);
    }

    /* ---------------------------------------------------------
       コンテキスト解放ラッパ
       --------------------------------------------------------- */
    void my_llama_free(struct llama_context *ctx)
    {
        llama_free(ctx);
    }

    /* ---------------------------------------------------------
       KVキャッシュ全消去ラッパ
       --------------------------------------------------------- */
    void my_llama_reset_kv(struct llama_context *ctx)
    {
        // 1. コンテキストからメモリ管理用ハンドルを取得
        llama_memory_t mem = llama_get_memory(ctx);

        // 2. メモリ領域をクリア (2番目の引数 bool は false: 通常のメモリクリア)
        llama_memory_clear(mem, false);
    }

    /* ---------------------------------------------------------
       vocab 取得ラッパ
       --------------------------------------------------------- */
    const struct llama_vocab *my_llama_model_get_vocab(struct llama_model *model)
    {
        return llama_model_get_vocab(model);
    }

    /* ---------------------------------------------------------
       推論ラッパ（llama_decode）
       --------------------------------------------------------- */
    int my_llama_eval(struct llama_context *ctx, const int32_t *tokens, int32_t n_tokens, int32_t n_past)
    {
        struct llama_batch batch = llama_batch_init(n_tokens, 0, 1);
        batch.n_tokens = n_tokens;

        for (int32_t i = 0; i < n_tokens; ++i)
        {
            batch.token[i] = (llama_token)tokens[i];
            batch.pos[i] = (llama_pos)(n_past + i);
            batch.n_seq_id[i] = 1;
            batch.seq_id[i][0] = 0;
            batch.logits[i] = (i == n_tokens - 1) ? 1 : 0;
        }

        int result = llama_decode(ctx, batch);
        llama_batch_free(batch);
        return result;
    }

    /* ---------------------------------------------------------
       修正版：KVキャッシュの部分削除 API (外科手術用)
       --------------------------------------------------------- */
    void llama_kv_cache_seq_rm_wrapper(struct llama_context *ctx, int32_t start_pos, int32_t end_pos)
    {
        llama_memory_t mem = llama_get_memory(ctx);
        llama_memory_seq_rm(mem, 0, (llama_pos)start_pos, (llama_pos)end_pos);
    }

    /* ---------------------------------------------------------
       トークンID→ピース変換ラッパ
       --------------------------------------------------------- */
    int my_llama_token_to_piece(struct llama_model *model, int token_id, char *buf, int length)
    {
        const struct llama_vocab *vocab = llama_model_get_vocab(model);
        return llama_token_to_piece(vocab, (llama_token)token_id, buf, (int32_t)length, 0, false);
    }

    /* ---------------------------------------------------------
       トークナイズラッパ
       --------------------------------------------------------- */
    int32_t my_llama_tokenize(const struct llama_vocab *vocab, const char *text, int32_t text_len,
                              int32_t *tokens, int32_t n_tokens_max, bool add_special, bool parse_special)
    {
        return llama_tokenize(vocab, text, text_len, (llama_token *)tokens, n_tokens_max, add_special, parse_special);
    }

    /* ---------------------------------------------------------
       EOS 判定ラッパ
       --------------------------------------------------------- */
    bool my_llama_is_eog(struct llama_context *ctx, int32_t token_id)
    {
        const struct llama_model *model = llama_get_model(ctx);
        const struct llama_vocab *vocab = llama_model_get_vocab(model);
        return llama_vocab_is_eog(vocab, (llama_token)token_id);
    }

    /* ---------------------------------------------------------
       サンプラーチェイン永続化 API
       --------------------------------------------------------- */
    struct llama_sampler *my_sampler_init(float temperature, float top_p)
    {
        struct llama_sampler_chain_params params = llama_sampler_chain_default_params();
        struct llama_sampler *chain = llama_sampler_chain_init(params);

        if (temperature > 0.0f)
        {
            llama_sampler_chain_add(chain, llama_sampler_init_temp(temperature));
        }
        if (top_p > 0.0f && top_p < 1.0f)
        {
            llama_sampler_chain_add(chain, llama_sampler_init_top_p(top_p, 1));
        }
        llama_sampler_chain_add(chain, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));

        return chain;
    }

    int32_t my_sampler_sample(struct llama_sampler *chain, struct llama_context *ctx)
    {
        return (int32_t)llama_sampler_sample(chain, ctx, -1);
    }

    void my_sampler_free(struct llama_sampler *chain)
    {
        if (chain)
        {
            llama_sampler_free(chain);
        }
    }

} // extern "C"
/*
cd ~/Chron-LLM

g++ -shared -fPIC -g -O0 \
    -I ~/llama.cpp/include \
    -I ~/llama.cpp/ggml/include \
    src/libllama_wrapper.cpp \
    -L ~/llama.cpp/build/bin \
    -lllama \
    -Wl,-rpath,'$ORIGIN' \
    -o ~/llama.cpp/build/bin/libllama_wrapper.so
*/