Let's assume you have a page item P1_FILE_BLOB (type File Browse) and a P1_RESULT_MESSAGE (Display Only) item.
SQL
DECLARE
    l_blob          BLOB;
    l_filename      VARCHAR2(255);
    l_mime_type     VARCHAR2(255);
    l_clob_response CLOB;
    l_status_code   NUMBER;
    l_is_blurry     VARCHAR2(10);
    l_variance_score NUMBER;
    l_error_message VARCHAR2(4000);
BEGIN
    -- Get file details from APEX file browse item
    SELECT blob_content, filename, mime_type
    INTO l_blob, l_filename, l_mime_type
    FROM apex_application_temp_files
    WHERE name = :P1_FILE_BLOB; -- Replace P1_FILE_BLOB with your actual file browse item name

    -- Clear any previous headers
    apex_web_service.g_request_headers.DELETE;

    -- Set Content-Type for multipart/form-data
    -- This is crucial for file uploads via APEX_WEB_SERVICE
    apex_web_service.g_request_headers(1).name := 'Content-Type';
    apex_web_service.g_request_headers(1).value := 'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'; -- Use a unique boundary

    -- Build the request body for multipart/form-data
    -- This part is a bit tricky, you need to manually construct the multipart body
    -- with the file content
    DECLARE
        l_body_clob CLOB;
        l_raw_data  RAW(32767); -- Buffer for BLOB chunks
        l_offset    INTEGER := 1;
        l_chunk_size CONSTANT INTEGER := 32767;
    BEGIN
        DBMS_LOB.CREATETEMPORARY(l_body_clob, TRUE);

        -- Part 1: Boundary
        DBMS_LOB.WRITEAPPEND(l_body_clob, LENGTH('------WebKitFormBoundary7MA4YWxkTrZu0gW' || CHR(13) || CHR(10)), '------WebKitFormBoundary7MA4YWxkTrZu0gW' || CHR(13) || CHR(10));
        -- Part 2: Content-Disposition for the file
        DBMS_LOB.WRITEAPPEND(l_body_clob, LENGTH('Content-Disposition: form-data; name="file"; filename="' || l_filename || '"' || CHR(13) || CHR(10)), 'Content-Disposition: form-data; name="file"; filename="' || l_filename || '"' || CHR(13) || CHR(10));
        -- Part 3: Content-Type of the file
        DBMS_LOB.WRITEAPPEND(l_body_clob, LENGTH('Content-Type: ' || l_mime_type || CHR(13) || CHR(10) || CHR(13) || CHR(10)), 'Content-Type: ' || l_mime_type || CHR(13) || CHR(10) || CHR(13) || CHR(10));

        -- Part 4: File BLOB content
        WHILE l_offset <= DBMS_LOB.GETLENGTH(l_blob) LOOP
            DBMS_LOB.READ(l_blob, l_chunk_size, l_offset, l_raw_data);
            DBMS_LOB.APPEND(l_body_clob, UTL_RAW.CAST_TO_VARCHAR2(l_raw_data)); -- Append RAW as VARCHAR2
            l_offset := l_offset + l_chunk_size;
        END LOOP;

        -- Part 5: Closing boundary
        DBMS_LOB.WRITEAPPEND(l_body_clob, LENGTH(CHR(13) || CHR(10) || '------WebKitFormBoundary7MA4YWxkTrZu0gW--' || CHR(13) || CHR(10)), CHR(13) || CHR(10) || '------WebKitFormBoundary7MA4YWxkTrZu0gW--' || CHR(13) || CHR(10));

        -- Make the POST request
        l_clob_response := apex_web_service.make_rest_request(
            p_url         => 'https://blur-d6ed.onrender.com/api/analyze_image', -- Replace with your actual Flask API URL
            p_http_method => 'POST',
            p_body        => l_body_clob,
            p_credential_static_id => 'YOUR_WEB_CREDENTIAL_STATIC_ID' -- Optional: if you have a web credential
        );

        l_status_code := apex_web_service.g_status_code;

        IF l_status_code = 200 THEN
            -- Parse the JSON response
            l_is_blurry := APEX_JSON.GET_VARCHAR2(p_text => l_clob_response, p_path => 'is_blurry');
            l_variance_score := APEX_JSON.GET_NUMBER(p_text => l_clob_response, p_path => 'blurriness_score');

            :P1_RESULT_MESSAGE := 'Result: Image is ' || l_is_blurry || '. Blurriness Score: ' || TO_CHAR(l_variance_score, 'fm999999999999990.00');
        ELSE
            l_error_message := APEX_JSON.GET_VARCHAR2(p_text => l_clob_response, p_path => 'error');
            :P1_RESULT_MESSAGE := 'Error from Flask API (' || l_status_code || '): ' || l_error_message;
        END IF;

        DBMS_LOB.FREETEMPORARY(l_body_clob); -- Free the temporary CLOB
    END;
EXCEPTION
    WHEN OTHERS THEN
        :P1_RESULT_MESSAGE := 'An unexpected error occurred: ' || SQLERRM;
        -- Optionally log the error details
END;
