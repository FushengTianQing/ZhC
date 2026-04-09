/**
 * zhc_fs.h - 文件系统库
 *
 * 提供完整的文件和目录操作功能：
 * - 目录创建、删除、遍历
 * - 文件属性查询
 * - 路径处理
 * - 文件系统操作（重命名、删除、复制）
 *
 * 版本: 1.0
 * 依赖: <sys/stat.h>, <dirent.h>, <unistd.h>, <libgen.h>
 */

#ifndef ZHC_FS_H
#define ZHC_FS_H

#include <stddef.h>
#include <sys/types.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ================================================================
 * 文件类型常量
 * ================================================================ */

/** 普通文件 */
#define ZHC_FILE_REGULAR   1
/** 目录 */
#define ZHC_FILE_DIRECTORY 2
/** 符号链接 */
#define ZHC_FILE_SYMLINK   3
/** 块设备 */
#define ZHC_FILE_BLOCK     4
/** 字符设备 */
#define ZHC_FILE_CHAR      5
/** 命名管道 */
#define ZHC_FILE_FIFO      6
/** 未知类型 */
#define ZHC_FILE_UNKNOWN   0

/* ================================================================
 * 类型定义
 * ================================================================ */

/**
 * 目录条目
 */
typedef struct {
    const char* name;  /* 条目名称 */
    int type;          /* 文件类型 */
} zhc_dirent_t;

/**
 * 文件状态
 */
typedef struct {
    long long size;     /* 文件大小（字节） */
    int mode;           /* 权限模式 */
    int uid;            /* 所有者用户ID */
    int gid;            /* 所有者组ID */
    long long atime;    /* 最后访问时间 */
    long long mtime;    /* 最后修改时间 */
    long long ctime;    /* 最后状态改变时间 */
    int blksize;        /* I/O 块大小 */
    long long blocks;   /* 分配的块数 */
} zhc_file_stat_t;

/* ================================================================
 * 目录操作
 * ================================================================ */

/**
 * zhc_mkdir - 创建目录
 *
 * 参数:
 *   path - 目录路径
 *   mode - 权限模式（如 0755）
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_mkdir(const char* path, int mode);

/**
 * zhc_mkdir_recursive - 创建多级目录
 *
 * 递归创建所有不存在的父目录
 *
 * 参数:
 *   path - 目录路径
 *   mode - 权限模式
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_mkdir_recursive(const char* path, int mode);

/**
 * zhc_rmdir - 删除空目录
 *
 * 参数:
 *   path - 目录路径
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_rmdir(const char* path);

/**
 * zhc_rmdir_recursive - 删除目录及其内容
 *
 * 递归删除目录及其所有内容
 *
 * 参数:
 *   path - 目录路径
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_rmdir_recursive(const char* path);

/**
 * zhc_opendir - 打开目录
 *
 * 参数:
 *   path - 目录路径
 *
 * 返回: 目录句柄（NULL 表示失败）
 */
void* zhc_opendir(const char* path);

/**
 * zhc_readdir - 读取目录条目
 *
 * 参数:
 *   dir  - 目录句柄
 *   entry - 输出条目
 *
 * 返回: 0 成功，-1 失败（读到末尾或出错）
 */
int zhc_readdir(void* dir, zhc_dirent_t* entry);

/**
 * zhc_closedir - 关闭目录
 *
 * 参数:
 *   dir - 目录句柄
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_closedir(void* dir);

/**
 * zhc_rewinddir - 重置目录位置
 *
 * 参数:
 *   dir - 目录句柄
 */
void zhc_rewinddir(void* dir);

/**
 * zhc_getcwd - 获取当前工作目录
 *
 * 参数:
 *   buffer - 输出缓冲区
 *   size   - 缓冲区大小
 *
 * 返回: buffer 成功，NULL 失败
 */
char* zhc_getcwd(char* buffer, size_t size);

/**
 * zhc_chdir - 切换工作目录
 *
 * 参数:
 *   path - 目标目录
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_chdir(const char* path);

/* ================================================================
 * 文件操作
 * ================================================================ */

/**
 * zhc_unlink - 删除文件
 *
 * 参数:
 *   path - 文件路径
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_unlink(const char* path);

/**
 * zhc_rename - 重命名文件或目录
 *
 * 参数:
 *   oldpath - 原路径
 *   newpath - 新路径
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_rename(const char* oldpath, const char* newpath);

/**
 * zhc_copyfile - 复制文件
 *
 * 参数:
 *   src - 源文件路径
 *   dst - 目标文件路径
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_copyfile(const char* src, const char* dst);

/**
 * zhc_movefile - 移动文件
 *
 * 参数:
 *   src - 源路径
 *   dst - 目标路径
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_movefile(const char* src, const char* dst);

/**
 * zhc_link - 创建硬链接
 *
 * 参数:
 *   target   - 目标文件路径
 *   linkname - 链接名称
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_link(const char* target, const char* linkname);

/**
 * zhc_symlink - 创建符号链接
 *
 * 参数:
 *   target   - 目标路径
 *   linkname - 链接名称
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_symlink(const char* target, const char* linkname);

/**
 * zhc_readlink - 读取符号链接内容
 *
 * 参数:
 *   path   - 符号链接路径
 *   buffer - 输出缓冲区
 *   size   - 缓冲区大小
 *
 * 返回: 读取的字节数，-1 失败
 */
int zhc_readlink(const char* path, char* buffer, size_t size);

/* ================================================================
 * 文件属性
 * ================================================================ */

/**
 * zhc_stat - 获取文件状态（通过路径）
 *
 * 参数:
 *   path - 文件路径
 *   stat - 输出状态
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_stat(const char* path, zhc_file_stat_t* stat);

/**
 * zhc_fstat - 获取文件状态（通过文件描述符）
 *
 * 参数:
 *   fd   - 文件描述符
 *   stat - 输出状态
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_fstat(int fd, zhc_file_stat_t* stat);

/**
 * zhc_lstat - 获取链接本身状态（不跟随符号链接）
 *
 * 参数:
 *   path - 链接路径
 *   stat - 输出状态
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_lstat(const char* path, zhc_file_stat_t* stat);

/**
 * zhc_chmod - 修改文件权限
 *
 * 参数:
 *   path - 文件路径
 *   mode - 新权限
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_chmod(const char* path, int mode);

/**
 * zhc_chown - 修改文件所有者
 *
 * 参数:
 *   path - 文件路径
 *   uid  - 用户ID（-1 表示不改变）
 *   gid  - 组ID（-1 表示不改变）
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_chown(const char* path, int uid, int gid);

/**
 * zhc_utime - 修改文件时间
 *
 * 参数:
 *   path  - 文件路径
 *   atime - 访问时间戳（-1 表示不改变）
 *   mtime - 修改时间戳（-1 表示不改变）
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_utime(const char* path, long long atime, long long mtime);

/**
 * zhc_file_exists - 判断文件是否存在
 *
 * 参数:
 *   path - 文件路径
 *
 * 返回: true 存在，false 不存在
 */
bool zhc_file_exists(const char* path);

/**
 * zhc_is_directory - 判断是否为目录
 *
 * 参数:
 *   path - 路径
 *
 * 返回: true 是目录，false 不是
 */
bool zhc_is_directory(const char* path);

/**
 * zhc_is_regular_file - 判断是否为普通文件
 *
 * 参数:
 *   path - 路径
 *
 * 返回: true 是普通文件，false 不是
 */
bool zhc_is_regular_file(const char* path);

/**
 * zhc_file_size - 获取文件大小
 *
 * 参数:
 *   path - 文件路径
 *
 * 返回: 文件大小（字节），-1 失败
 */
long long zhc_file_size(const char* path);

/* ================================================================
 * 路径处理
 * ================================================================ */

/**
 * zhc_path_join - 拼接路径
 *
 * 将多个路径部分拼接为一个路径
 *
 * 参数:
 *   buffer - 输出缓冲区
 *   size   - 缓冲区大小
 *   ...    - 路径部分（以 NULL 结尾）
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_path_join(char* buffer, size_t size, ...);

/**
 * zhc_path_normalize - 规范化路径
 *
 * 消除 . 和 .. ，转换为绝对路径
 *
 * 参数:
 *   path   - 输入路径
 *   buffer - 输出缓冲区
 *   size   - 缓冲区大小
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_path_normalize(const char* path, char* buffer, size_t size);

/**
 * zhc_path_absolute - 获取绝对路径
 *
 * 参数:
 *   relpath - 相对路径
 *   buffer  - 输出缓冲区
 *   size    - 缓冲区大小
 *
 * 返回: 0 成功，-1 失败
 */
int zhc_path_absolute(const char* relpath, char* buffer, size_t size);

/**
 * zhc_path_dirname - 获取目录名
 *
 * 参数:
 *   path   - 输入路径
 *   buffer - 输出缓冲区
 *   size   - 缓冲区大小
 *
 * 返回: buffer
 */
char* zhc_path_dirname(const char* path, char* buffer, size_t size);

/**
 * zhc_path_basename - 获取文件名
 *
 * 参数:
 *   path   - 输入路径
 *   buffer - 输出缓冲区
 *   size   - 缓冲区大小
 *
 * 返回: buffer
 */
char* zhc_path_basename(const char* path, char* buffer, size_t size);

/**
 * zhc_path_extname - 获取文件扩展名
 *
 * 参数:
 *   path - 文件路径
 *
 * 返回: 扩展名（含点号），无扩展名返回空字符串
 */
const char* zhc_path_extname(const char* path);

/**
 * zhc_path_remove_ext - 去除扩展名
 *
 * 参数:
 *   path   - 输入路径
 *   buffer - 输出缓冲区
 *   size   - 缓冲区大小
 *
 * 返回: buffer
 */
char* zhc_path_remove_ext(const char* path, char* buffer, size_t size);

/**
 * zhc_path_is_absolute - 判断是否为绝对路径
 *
 * 参数:
 *   path - 路径
 *
 * 返回: true 是绝对路径，false 不是
 */
bool zhc_path_is_absolute(const char* path);

/* ================================================================
 * 实现
 * ================================================================ */

#ifdef ZHC_FS_IMPLEMENTATION

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <dirent.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <unistd.h>
#include <libgen.h>
#include <stdarg.h>
#include <fcntl.h>
#include <utime.h>

/* ---------- 目录操作 ---------- */

int zhc_mkdir(const char* path, int mode) {
    return mkdir(path, (mode_t)mode);
}

int zhc_mkdir_recursive(const char* path, int mode) {
    char tmp[512];
    char* p = NULL;
    size_t len;

    if (snprintf(tmp, sizeof(tmp), "%s", path) >= (int)sizeof(tmp)) {
        return -1;
    }
    len = strlen(tmp);

    if (len > 0 && tmp[len - 1] == '/') {
        tmp[len - 1] = '\0';
    }

    for (p = tmp + 1; *p; p++) {
        if (*p == '/') {
            *p = '\0';
            if (mkdir(tmp, (mode_t)mode) != 0 && errno != EEXIST) {
                return -1;
            }
            *p = '/';
        }
    }

    if (mkdir(tmp, (mode_t)mode) != 0 && errno != EEXIST) {
        return -1;
    }
    return 0;
}

int zhc_rmdir(const char* path) {
    return rmdir(path);
}

int zhc_rmdir_recursive(const char* path) {
    DIR* dir = opendir(path);
    if (dir == NULL) {
        return -1;
    }

    struct dirent* entry;
    char subpath[512];

    while ((entry = readdir(dir)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }

        if (snprintf(subpath, sizeof(subpath), "%s/%s", path, entry->d_name)
            >= (int)sizeof(subpath)) {
            closedir(dir);
            return -1;
        }

        if (entry->d_type == DT_DIR) {
            if (zhc_rmdir_recursive(subpath) != 0) {
                closedir(dir);
                return -1;
            }
        } else {
            if (unlink(subpath) != 0) {
                closedir(dir);
                return -1;
            }
        }
    }

    closedir(dir);
    return rmdir(path);
}

void* zhc_opendir(const char* path) {
    return (void*)opendir(path);
}

int zhc_readdir(void* dir, zhc_dirent_t* entry) {
    struct dirent* de = readdir((DIR*)dir);
    if (de == NULL) {
        return -1;
    }

    entry->name = de->d_name;

    switch (de->d_type) {
        case DT_REG:  entry->type = ZHC_FILE_REGULAR; break;
        case DT_DIR:  entry->type = ZHC_FILE_DIRECTORY; break;
        case DT_LNK:  entry->type = ZHC_FILE_SYMLINK; break;
        case DT_BLK:  entry->type = ZHC_FILE_BLOCK; break;
        case DT_CHR:  entry->type = ZHC_FILE_CHAR; break;
        case DT_FIFO: entry->type = ZHC_FILE_FIFO; break;
        default:      entry->type = ZHC_FILE_UNKNOWN; break;
    }

    return 0;
}

int zhc_closedir(void* dir) {
    return closedir((DIR*)dir);
}

void zhc_rewinddir(void* dir) {
    rewinddir((DIR*)dir);
}

char* zhc_getcwd(char* buffer, size_t size) {
    return getcwd(buffer, size);
}

int zhc_chdir(const char* path) {
    return chdir(path);
}

/* ---------- 文件操作 ---------- */

int zhc_unlink(const char* path) {
    return unlink(path);
}

int zhc_rename(const char* oldpath, const char* newpath) {
    return rename(oldpath, newpath);
}

int zhc_copyfile(const char* src, const char* dst) {
    FILE* srcf = fopen(src, "rb");
    if (srcf == NULL) {
        return -1;
    }

    FILE* dstf = fopen(dst, "wb");
    if (dstf == NULL) {
        fclose(srcf);
        return -1;
    }

    char buf[8192];
    size_t n;

    while ((n = fread(buf, 1, sizeof(buf), srcf)) > 0) {
        if (fwrite(buf, 1, n, dstf) != n) {
            fclose(srcf);
            fclose(dstf);
            unlink(dst);
            return -1;
        }
    }

    fclose(srcf);
    fclose(dstf);
    return 0;
}

int zhc_movefile(const char* src, const char* dst) {
    if (rename(src, dst) == 0) {
        return 0;
    }

    if (errno == EXDEV) {
        if (zhc_copyfile(src, dst) != 0) {
            return -1;
        }
        if (unlink(src) != 0) {
            unlink(dst);
            return -1;
        }
        return 0;
    }

    return -1;
}

int zhc_link(const char* target, const char* linkname) {
    return link(target, linkname);
}

int zhc_symlink(const char* target, const char* linkname) {
    return symlink(target, linkname);
}

int zhc_readlink(const char* path, char* buffer, size_t size) {
    return (int)readlink(path, buffer, size);
}

/* ---------- 文件属性 ---------- */

static void stat_to_zhc_stat(const struct stat* st, zhc_file_stat_t* out) {
    out->size = (long long)st->st_size;
    out->mode = (int)st->st_mode;
    out->uid = (int)st->st_uid;
    out->gid = (int)st->st_gid;
    out->atime = (long long)st->st_atime;
    out->mtime = (long long)st->st_mtime;
    out->ctime = (long long)st->st_ctime;
    out->blksize = (int)st->st_blksize;
    out->blocks = (long long)st->st_blocks;
}

int zhc_stat(const char* path, zhc_file_stat_t* stat_out) {
    struct stat st;
    if (stat(path, &st) != 0) {
        return -1;
    }
    stat_to_zhc_stat(&st, stat_out);
    return 0;
}

int zhc_fstat(int fd, zhc_file_stat_t* stat) {
    struct stat st;
    if (fstat(fd, &st) != 0) {
        return -1;
    }
    stat_to_zhc_stat(&st, stat);
    return 0;
}

int zhc_lstat(const char* path, zhc_file_stat_t* stat_out) {
    struct stat st;
    if (lstat(path, &st) != 0) {
        return -1;
    }
    stat_to_zhc_stat(&st, stat_out);
    return 0;
}

int zhc_chmod(const char* path, int mode) {
    return chmod(path, (mode_t)mode);
}

int zhc_chown(const char* path, int uid, int gid) {
    return chown(path, (uid_t)uid, (gid_t)gid);
}

int zhc_utime(const char* path, long long atime, long long mtime) {
    struct utimbuf times;
    times.actime = (time_t)atime;
    times.modtime = (time_t)mtime;
    return utime(path, &times);
}

bool zhc_file_exists(const char* path) {
    struct stat st;
    return stat(path, &st) == 0;
}

bool zhc_is_directory(const char* path) {
    struct stat st;
    if (stat(path, &st) != 0) {
        return false;
    }
    return S_ISDIR(st.st_mode);
}

bool zhc_is_regular_file(const char* path) {
    struct stat st;
    if (stat(path, &st) != 0) {
        return false;
    }
    return S_ISREG(st.st_mode);
}

long long zhc_file_size(const char* path) {
    struct stat st;
    if (stat(path, &st) != 0) {
        return -1;
    }
    return (long long)st.st_size;
}

/* ---------- 路径处理 ---------- */

int zhc_path_join(char* buffer, size_t size, ...) {
    va_list args;
    va_start(args, size);

    buffer[0] = '\0';
    size_t len = 0;

    const char* part;
    while ((part = va_arg(args, const char*)) != NULL) {
        size_t part_len = strlen(part);

        /* 跳过空部分 */
        if (part_len == 0) {
            continue;
        }

        /* 确定是否需要加分隔符 */
        if (len > 0) {
            int needs_sep = 1;
            /* 如果 buffer 末尾已经是 /，不需要分隔符 */
            if (buffer[len - 1] == '/') {
                needs_sep = 0;
            }
            /* 如果 part 开头是 /，不需要分隔符（且去掉开头的/） */
            if (part[0] == '/') {
                needs_sep = 0;
                part++;
                part_len--;
                if (part_len == 0) {
                    continue;
                }
            }
            if (needs_sep) {
                if (len + 1 >= size) {
                    va_end(args);
                    return -1;
                }
                buffer[len++] = '/';
            }
        } else if (part[0] == '/') {
            /* 第一个部分以 / 开头，保留它 */
            if (len + 1 >= size) {
                va_end(args);
                return -1;
            }
            buffer[len++] = '/';
            part++;
            part_len--;
            if (part_len == 0) {
                continue;
            }
        }

        if (len + part_len >= size) {
            va_end(args);
            return -1;
        }

        strncpy(buffer + len, part, part_len);
        len += part_len;
        buffer[len] = '\0';
    }

    va_end(args);
    return 0;
}

int zhc_path_normalize(const char* path, char* buffer, size_t size) {
    char* resolved = realpath(path, buffer);
    if (resolved == NULL) {
        return -1;
    }
    return 0;
}

int zhc_path_absolute(const char* relpath, char* buffer, size_t size) {
    if (zhc_path_is_absolute(relpath)) {
        if (strlen(relpath) >= size) {
            return -1;
        }
        strcpy(buffer, relpath);
        return 0;
    }

    char cwd[512];
    if (zhc_getcwd(cwd, sizeof(cwd)) == NULL) {
        return -1;
    }

    if (snprintf(buffer, size, "%s/%s", cwd, relpath) >= (int)size) {
        return -1;
    }

    char normalized[512];
    if (zhc_path_normalize(buffer, normalized, sizeof(normalized)) != 0) {
        return -1;
    }

    strncpy(buffer, normalized, size - 1);
    buffer[size - 1] = '\0';
    return 0;
}

char* zhc_path_dirname(const char* path, char* buffer, size_t size) {
    char tmp[512];
    if (strlen(path) >= sizeof(tmp)) {
        buffer[0] = '\0';
        return buffer;
    }
    strcpy(tmp, path);

    char* dir = dirname(tmp);
    strncpy(buffer, dir, size - 1);
    buffer[size - 1] = '\0';
    return buffer;
}

char* zhc_path_basename(const char* path, char* buffer, size_t size) {
    char tmp[512];
    if (strlen(path) >= sizeof(tmp)) {
        buffer[0] = '\0';
        return buffer;
    }
    strcpy(tmp, path);

    char* base = basename(tmp);
    strncpy(buffer, base, size - 1);
    buffer[size - 1] = '\0';
    return buffer;
}

const char* zhc_path_extname(const char* path) {
    const char* dot = strrchr(path, '.');
    if (dot == NULL || dot == path) {
        return "";
    }
    return dot;
}

char* zhc_path_remove_ext(const char* path, char* buffer, size_t size) {
    size_t len = strlen(path);
    if (len >= size) {
        buffer[0] = '\0';
        return buffer;
    }

    const char* ext = zhc_path_extname(path);
    size_t ext_len = strlen(ext);

    if (ext_len == 0) {
        strcpy(buffer, path);
    } else {
        size_t copy_len = len - ext_len;
        strncpy(buffer, path, copy_len);
        buffer[copy_len] = '\0';
    }

    return buffer;
}

bool zhc_path_is_absolute(const char* path) {
    return path != NULL && path[0] == '/';
}

#endif /* ZHC_FS_IMPLEMENTATION */

#ifdef __cplusplus
}
#endif

#endif /* ZHC_FS_H */
