DELETE *
FROM yq.xyfxzs b
    LEFT JOIN temp_ids ti ON b.id = ti.id
WHERE ti.id IS NULL;