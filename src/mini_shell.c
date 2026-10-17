#define _POSIX_C_SOURCE 200809L
#include <ctype.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define MAX_LINE 1024
#define MAX_ARGS 64
#define MAX_JOBS 128

typedef struct {
    int id;
    pid_t pid;
    char command[MAX_LINE];
    int active;
} Job;

static Job jobs[MAX_JOBS];
static int next_job_id = 1;

static void reap_jobs(void) {
    for (int i = 0; i < MAX_JOBS; i++) {
        if (jobs[i].active) {
            int status;
            pid_t r = waitpid(jobs[i].pid, &status, WNOHANG);
            if (r == jobs[i].pid || (r == -1 && errno == ECHILD)) {
                printf("[job %d] PID %ld completed\n", jobs[i].id, (long)jobs[i].pid);
                jobs[i].active = 0;
            }
        }
    }
}

static void show_jobs(void) {
    reap_jobs();
    int found = 0;
    puts("JOB_ID   PID       STATUS    COMMAND");
    for (int i = 0; i < MAX_JOBS; i++) {
        if (jobs[i].active) {
            printf("%-8d %-9ld RUNNING   %s\n", jobs[i].id, (long)jobs[i].pid, jobs[i].command);
            found = 1;
        }
    }
    if (!found) puts("(no active background jobs)");
}

static int add_job(pid_t pid, const char *command) {
    for (int i = 0; i < MAX_JOBS; i++) {
        if (!jobs[i].active) {
            jobs[i].id = next_job_id++;
            jobs[i].pid = pid;
            snprintf(jobs[i].command, sizeof(jobs[i].command), "%s", command);
            jobs[i].active = 1;
            printf("[%d] %ld\n", jobs[i].id, (long)pid);
            return jobs[i].id;
        }
    }
    fprintf(stderr, "Job table is full; cannot track another background job.\n");
    return -1;
}

static void print_help(void) {
    puts("Mini Linux Shell - supported commands:");
    puts("  help                 Show this help");
    puts("  pwd, date, whoami    Basic system commands");
    puts("  ls [directory]       List files");
    puts("  echo [text...]       Print text");
    puts("  sleep SECONDS        Wait for a duration");
    puts("  cd [directory]       Change current directory");
    puts("  jobs                 List background jobs");
    puts("  kill JOB_ID          Terminate a tracked background job");
    puts("  command &            Run supported external command in background");
    puts("  exit / quit          Exit shell");
    puts("This is a teaching shell; pipes, redirects and command chaining are not implemented.");
}

static int is_allowed(const char *cmd) {
    const char *allowed[] = {"pwd", "date", "whoami", "hostname", "ls", "echo", "sleep", "uptime", "uname"};
    for (size_t i = 0; i < sizeof(allowed) / sizeof(allowed[0]); i++) {
        if (strcmp(cmd, allowed[i]) == 0) return 1;
    }
    return 0;
}

static void terminate_job(const char *arg) {
    char *end = NULL;
    long id = strtol(arg, &end, 10);
    if (arg[0] == '\0' || !end || *end != '\0' || id <= 0) {
        fprintf(stderr, "Usage: kill JOB_ID\n");
        return;
    }
    for (int i = 0; i < MAX_JOBS; i++) {
        if (jobs[i].active && jobs[i].id == (int)id) {
            if (kill(jobs[i].pid, SIGTERM) == -1) {
                perror("kill");
                return;
            }
            printf("Sent SIGTERM to job %d (PID %ld)\n", jobs[i].id, (long)jobs[i].pid);
            int status;
            if (waitpid(jobs[i].pid, &status, 0) == -1 && errno != ECHILD) perror("waitpid");
            jobs[i].active = 0;
            return;
        }
    }
    fprintf(stderr, "No active job with ID %ld\n", id);
}

int main(void) {
    char line[MAX_LINE];
    signal(SIGINT, SIG_IGN);
    puts("Mini Linux Shell with Background Job Management");
    puts("Type 'help' for commands. Only allowlisted commands are supported.");
    for (;;) {
        reap_jobs();
        printf("mini-shell$ ");
        fflush(stdout);
        if (!fgets(line, sizeof(line), stdin)) {
            putchar('\n');
            break;
        }
        line[strcspn(line, "\n")] = '\0';
        char original[MAX_LINE];
        snprintf(original, sizeof(original), "%s", line);

        char *args[MAX_ARGS];
        int argc = 0;
        char *save = NULL;
        char *token = strtok_r(line, " \t", &save);
        while (token && argc < MAX_ARGS - 1) {
            args[argc++] = token;
            token = strtok_r(NULL, " \t", &save);
        }
        args[argc] = NULL;
        if (argc == 0) continue;

        if (strcmp(args[0], "exit") == 0 || strcmp(args[0], "quit") == 0) break;
        if (strcmp(args[0], "help") == 0) { print_help(); continue; }
        if (strcmp(args[0], "jobs") == 0) { show_jobs(); continue; }
        if (strcmp(args[0], "kill") == 0) {
            if (argc != 2) fprintf(stderr, "Usage: kill JOB_ID\n");
            else terminate_job(args[1]);
            continue;
        }
        if (strcmp(args[0], "cd") == 0) {
            const char *dir = argc > 1 ? args[1] : getenv("HOME");
            if (!dir || chdir(dir) != 0) perror("cd");
            continue;
        }

        int background = 0;
        if (argc > 0 && strcmp(args[argc - 1], "&") == 0) {
            background = 1;
            args[--argc] = NULL;
        } else if (argc > 0) {
            size_t len = strlen(args[argc - 1]);
            if (len > 1 && args[argc - 1][len - 1] == '&') {
                args[argc - 1][len - 1] = '\0';
                background = 1;
                if (args[argc - 1][0] == '\0') args[--argc] = NULL;
            }
        }
        if (argc == 0) continue;
        if (!is_allowed(args[0])) {
            fprintf(stderr, "Command '%s' is not in the allowlist. Type 'help'.\n", args[0]);
            continue;
        }

        pid_t pid = fork();
        if (pid < 0) { perror("fork"); continue; }
        if (pid == 0) {
            signal(SIGINT, SIG_DFL);
            execvp(args[0], args);
            perror("execvp");
            _exit(127);
        }
        if (background) {
            if (add_job(pid, original) < 0) {
                kill(pid, SIGTERM);
                waitpid(pid, NULL, 0);
            }
        } else {
            int status;
            while (waitpid(pid, &status, 0) == -1) {
                if (errno == EINTR) continue;
                perror("waitpid");
                break;
            }
        }
    }

    for (int i = 0; i < MAX_JOBS; i++) {
        if (jobs[i].active) {
            kill(jobs[i].pid, SIGTERM);
            waitpid(jobs[i].pid, NULL, 0);
        }
    }
    puts("Mini shell exited.");
    return 0;
}
