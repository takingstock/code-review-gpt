#ifndef TREE_SITTER_NODEJS_TS_H_
#define TREE_SITTER_NODEJS_TS_H_

typedef struct TSLanguage TSLanguage;

#ifdef __cplusplus
extern "C" {
#endif

const TSLanguage *tree_sitter_nodejs_ts(void);

#ifdef __cplusplus
}
#endif

#endif // TREE_SITTER_NODEJS_TS_H_
