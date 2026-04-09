#define ZHC_NET_IMPLEMENTATION
#include "zhc_net.h"
#include <stdio.h>
#include <string.h>

int main() {
    printf("Testing HTTP POST to httpbin.org...\n");

    zhc_http_response_t* resp = zhc_http_post(
        "http://httpbin.org/post",
        "name=test&value=123",
        "application/x-www-form-urlencoded"
    );
    if (resp == NULL) {
        printf("http_post failed\n");
        return 1;
    }

    printf("status_code: %d\n", resp->status_code);
    printf("status_text: %s\n", resp->status_text ? resp->status_text : "NULL");
    printf("content_length: %d\n", resp->content_length);
    printf("content_type: %s\n", resp->content_type ? resp->content_type : "NULL");
    printf("content: %s\n", resp->content ? "PRESENT" : "NULL");

    if (resp->content) {
        printf("\n--- Content Preview (first 500 chars) ---\n");
        int preview_len = resp->content_length < 500 ? resp->content_length : 500;
        printf("%.*s\n", preview_len, resp->content);
    }

    zhc_http_response_free(resp);
    printf("\nOK\n");
    return 0;
}