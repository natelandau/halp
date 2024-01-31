# This is a sample document containing
# 3 exports
# 3 functions
# 3 aliases
# 4 with code="hello world"

EXPORT export1="$PATH:/usr/local/bin"
alias alias1='some code that does something' # comment 1

# Always print contents of directory when entering
func1() {
    builtin cd "$@" || return 1
    ls -alF
}
export export2="Hello World"

    function func2() {
        echo "Hello World";
    }

alias alias2='ls -l' # comment 2

# shellcheck disable=SC1054
function func3() {echo "Hello World"; }

alias alias3='la -l'
# test

export EXPORT3="Hello World"

# Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
