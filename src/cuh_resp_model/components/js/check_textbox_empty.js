(val, _) => {
    // No error (false) if value is truish, else error message
    // val assumed to be string or null
    return val ? false : "Input must be non-empty."
}