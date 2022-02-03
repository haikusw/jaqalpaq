#!/bin/bash
set -e

# This script is provided to assit in development installations of JaqalPaq.
# The code is either "self-documenting", inline-documented or undocumented.

# The install script allows the selection of a customized set of features of
# JaqalPaq to install.  Set JAQALPAQ_OPTS and/or JAQALPAQ_EXTRAS_OPTS to
# enable various extras, e.g., pyGSTi integration (by default, enabled).

if [ -n "${JAQALPAQ_OPTS+x}" ] ; then
    [ -n "${JAQALPAQ_OPTS}" ] &&
        JAQALPAQ_OPTS="[$JAQALPAQ_OPTS]"
else
    JAQALPAQ_OPTS="[pygsti-integration]"
fi

if [ -n "${JAQALPAQ_EXTRAS_OPTS+x}" ] ; then
    [ -n "${JAQALPAQ_EXTRAS_OPTS}" ] &&
        JAQALPAQ_EXTRAS_OPTS="[$JAQALPAQ_EXTRAS_OPTS]"
else
    JAQALPAQ_EXTRAS_OPTS="[qiskit,pyquil,cirq,projectq,pytket,tutorial]"
fi

if [ -n "${QSCOUT_GATEMODELS_OPTS+x}" ] ; then
    [ -n "${QSCOUT_GATEMODELS_OPTS}" ] &&
        QSCOUT_GATEMODELS_OPTS="[$JAQALPAQ_EXTRAS_OPTS]"
else
    QSCOUT_GATEMODELS_OPTS=""
fi

if [ "${DISABLE_CYTHON=0}" = "0" ] ; then
    if ! python3-config --includes >/dev/null ; then
        echo "You do not have the Python 3 development headers installed."
        echo "If you are running a Debian (or derivative), this can be"
        echo "fixed by running:"
        echo ""
        echo "    # apt install python3-dev"
        echo ""
        echo "One yum-based systems, run:"
        echo ""
        echo "    # yum install python3-devel"
        echo ""
        echo "This should not happen within a Conda installation."
        echo ""
        echo "Alternatively, you can set \$DISABLE_CYTHON=1"
        exit 1
    fi
else
    echo "Cython extensions are disabled."
    echo "Set PYGSTI_NO_CYTHON_WARNING to suppress further warnings."
fi

# Set the LOCAL_* environment variables to select a local repository to
# install from, rather than pulling from pyPI.

# Alternatively, setting these environment variables to the empty string
# will suppress its installation entirely.

declare -a args
args=()

if [ -n "${LOCAL_PYGSTI}" ] ; then
    args+=(-e "${LOCAL_PYGSTI}")
fi

if [ -n "${LOCAL_JAQALPAQ+x}" ] ; then
    [ -n "$LOCAL_JAQALPAQ" ] &&
        args+=(-e "${LOCAL_JAQALPAQ}${JAQALPAQ_OPTS}")
else
    args+=("JaqalPaq${JAQALPAQ_OPTS}")
fi

if [ -n "${LOCAL_JAQALPAQ_EXTRAS+x}" ] ; then
    [ -n "$LOCAL_JAQALPAQ_EXTRAS" ] &&
        args+=(-e "${LOCAL_JAQALPAQ_EXTRAS}${JAQALPAQ_EXTRAS_OPTS}")
else
    args+=("JaqalPaq-extras${JAQALPAQ_EXTRAS_OPTS}")
fi

if [ -n "${LOCAL_QSCOUT_GATEMODELS+x}" ] ; then
    [ -n "$LOCAL_QSCOUT_GATEMODELS" ] &&
        args+=(-e "${LOCAL_QSCOUT_GATEMODELS}${QSCOUT_GATEMODELS_OPTS}")
else
    args+=("QSCOUT-gatemodels${QSCOUT_GATEMODELS_OPTS}")
fi

pip install "${args[@]}"

echo "=============================="
echo "      Install Succeeded!"
echo "=============================="
