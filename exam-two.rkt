
;                                                                                 
;                                                                                 
;                                                                                 
;   ;        ;;;    ;     ;    ;;;    ;;;;;;   ;;;;  ;;;;;;;    ;  ;     ; ;;;;;;;
;   ;       ;   ;   ;;    ;   ;   ;   ;       ;    ;    ;       ;  ;;    ;    ;   
;   ;      ;     ;  ; ;   ;  ;     ;  ;       ;    ;    ;       ;  ; ;   ;    ;   
;   ;      ;     ;  ; ;   ;  ;        ;       ;         ;       ;  ; ;   ;    ;   
;   ;      ;     ;  ;  ;  ;  ;   ;;;  ;;;;;;   ;;;;     ;       ;  ;  ;  ;    ;   
;   ;      ;     ;  ;   ; ;  ;     ;  ;            ;    ;       ;  ;   ; ;    ;   
;   ;      ;     ;  ;   ; ;  ;     ;  ;       ;    ;    ;       ;  ;   ; ;    ;   
;   ;       ;   ;   ;    ;;   ;   ;   ;       ;    ;    ;       ;  ;    ;;    ;   
;   ;;;;;;   ;;;    ;     ;    ;;;    ;;;;;;   ;;;;     ;       ;  ;     ;    ;   
;                                                                                 
;                                                                                 
;                                                                                 

;; vector -> int
;; Purpose: find the number of digits in the largest number in the vector.
(define (longest-int-len a-vector)
  (local
    [;; int int -> int
     ;; Purpose: Return the length of the number
     ;; How: The function calls itself with the input integer's quotient when divided by 10 and the accumulator incremented by one. Once the
     ;; quotient of the integer and 10 is equal to 0, the function has divided the input integer the same number of times as the total number of digits
     ;; in the original input. The function returns the accumulator and terminates.
     ;; Termination argument: The function will always terminate because once any number is divided by 10 enough times, the quotient must be 0.
     ;; Accumulator invariant: accum = number of digits in the proccessed part of the integer
     (define (int-len a-int accum)
       (if (= a-int 0)
           accum
           (int-len (quotient a-int 10) (add1 accum))))
     ;; vector int int -> int
     ;; Purpose: Return the number with the longest length
     ;; How: The number at the index is compared with the current highest number. If the number at the index is larger
     ;;      than the current highest number, function is called again with the index incremented by 1
     ;;      and the highest is replaced with the new highest number. Otherwise, the function is called again with the index incremented
     ;;      by one and the same highest number. Once the index is equal to the vector length, the function returns the highest and terminates.
     ;; Termination argument: This function will always terminate because every call increments the index by 1 and the function terminates
     ;; and returns the highest when index equals the vector length. The index always starts at 0 and must eventually reach the vector length when
     ;; incremented by 1.
     ;; Accumulator invariant: index = the index of the element in the vector which is being proccessed.
     ;;                        highest = largest number in [0..index]
     (define (longest-int-len-helper a-vector highest index)
       (if (= (vector-length a-vector) index)
           highest
           (local [(define current-num (abs (vector-ref a-vector index)))]
             (if (> current-num highest)
                 (longest-int-len-helper a-vector current-num (add1 index))
                 (longest-int-len-helper a-vector highest (add1 index))))))]
    (int-len (longest-int-len-helper a-vector (vector-ref a-vector 0) 0) 0)))

;; Sample values
(define V1 (vector 1082 45 -9097432623 64 765 876532))
(define V2 (vector 1082 45 -1239 64 765 876532))
(define V3 (vector 1082 45 128736 64 76123865 876532))
;; tests using sample values
(check-expect (longest-int-len V1) 10)
(check-expect (longest-int-len V2) 6)
(check-expect (longest-int-len V3) 8)


;                                                   
;                                                   
;                                                   
;   ;;;;;   ;     ;    ;;;    ;     ; ;;;;;; ;;;;;;;
;   ;    ;  ;     ;   ;   ;   ;    ;  ;         ;   
;   ;    ;  ;     ;  ;     ;  ;   ;   ;         ;   
;   ;    ;  ;     ;  ;        ;  ;    ;         ;   
;   ;;;;;;  ;     ;  ;        ; ;     ;;;;;;    ;   
;   ;    ;  ;     ;  ;        ;; ;    ;         ;   
;   ;    ;  ;     ;  ;     ;  ;   ;   ;         ;   
;   ;    ;   ;   ;    ;   ;   ;    ;  ;         ;   
;   ;;;;;     ;;;      ;;;    ;     ; ;;;;;;    ;   
;                                                   
;                                                   
;                                                   


;; --> bucket
;; Purpose: To construct a bank account
;; A bucket is an interface offering
;; 'add: integer -> (void)
;; 'initialize-bucket!: vector -> (void)
;; 'dump: branch -> (void)
;; 'size: -> integer
;; 'elems: --> vector
(define (bucket)
  (local [;; vector
          ;; Purpose: Store the elements of the bucket
          (define a-bucket 'uninitialized)
          ;; vector → (void) throws error
          ;; Purpose: Initialize a-bucket
          ;; Effect: a-bucket is mutated to the given vector
          (define (initialize-bucket! vointegers)
            (if (not (vector? vointegers))
                (error
                 'initialize-bucket!
                 "Bucket cannot be initialized to a non-vector")
                (set! a-bucket vointegers)))
          ;; integer → (void) throws error
          ;; Purpose: To add the given integer to the bucket
          ;; Effect: The given integer is added to the bucket vector
          (define (add! a-int)
            (local [(define temp-vector (make-vector (add1 (vector-length a-bucket)) void))
                    ;; vector integer -> vector
                    ;; Purpose: Take the input vector and mutate the first elements to match those
                    ;;          of the bucket.
                    ;; How: Recursively call the function with the element in the input vector at index mutated to the value of the element
                    ;;      in the bucket at the same index. Increase the index by one and recursively call the function
                    ;;      until the index equals the length of the bucket. Then, return the vector.
                    ;; Termination argument: This function will always terminate because each call increments the index by one. The index
                    ;;                       starts at 0, so it must eventually reach the length of the bucket. When this happens, the function terminates.
                    ;; Accumulator invariant: index = the index of the element in the input vector which is being proccessed.
                    ;; Effect: the given vector is returned with the first (vector-length a-bucket) elements in the given vector
                    ;; elements matching the first (vector-length a-bucket) in the bucket.
                    (define (repop-vector a-vector index)
                      (if (= index (vector-length a-bucket))
                          a-vector
                          (repop-vector (begin (vector-set! a-vector index (vector-ref a-bucket index)) a-vector) (add1 index))))]
              (begin
                (vector-set! temp-vector (vector-length a-bucket) a-int)
                (set! a-bucket (repop-vector temp-vector 0)))))
          ;; vector integer -> vector
          ;; Purpose: Take the elements of the bucket and dump them into the given vector starting at the index. Then empty the bucket.
          ;; Accumulator invariant: index = the index of the element in the input vector which is being proccessed.
          ;; Effect: The bucket's elements are added to the input vector and the bucket is empty.
          (define (dump! a-vector index)
            (local
              [;; vector integer integer -> posn
               ;; Purpose: Take the given vector and add the elements from the bucket to it starting at index1.
               ;; Accumulator invariant: index1 = Index of a-vector to add the element to.
               ;;                        index2 = Index of the element in a-bucket to add to a-vector.
               ;; How: Take the element from index2 in bucket and add it to index1 in the vector. The function will recursively call itself
               ;;      with index1 and index2 incremented by 1 until index2 is equal to the length of the bucket. This indicates every element of
               ;;      the bucket has been traversed. At this point, return a posn with the posn-x as the new vector and posn-y as the call to uninitializing
               ;;      the bucket (to hide "void" from the return).
               ;; Termination argument: This function will always terminate because with every call to repop-vector-gen, the index2 is incremented by 1.
               ;;                       This function should always be called with index2 as 0, and if 0 is incremented by one, it should always reach
               ;;                       the length of the bucket, at which point the function terminates.
               (define (repop-vector-gen a-vector index1 index2)
                 (if (= index2 (vector-length a-bucket))
                     (make-posn a-vector (set! a-bucket 'uninitialized))
                     (repop-vector-gen (begin (vector-set! a-vector index1 (vector-ref a-bucket index2)) a-vector) (add1 index1) (add1 index2))))]
              (posn-x (repop-vector-gen a-vector index 0))
              ))
          ;; --> integer
          ;; Purpose: Return the number of elements in the bucket.
          (define (size)
            (vector-length a-bucket))
          ;; --> vector
          ;; Purpose: Return an vector containing the elements in the bucket.
          (define (elems)
            a-bucket)
          ;; message → ba
          ;; Purpose: To manage bank account services
          (define (bucket-object a-message)
            (cond [(eq? a-message 'add) add!]
                  [(eq? a-message 'init) initialize-bucket!]
                  [(eq? a-message 'dump) dump!]
                  [(eq? a-message 'size) size]
                  [(eq? a-message 'elems) elems]
                  [else
                   (error 'bucket-object
                          (format "Unknown message received: ~s"
                                  a-message))]))]
    bucket-object))


;                                                                         
;                                                                         
;                                                                         
;   ;;;;;;     ;    ;;;;;    ; ;     ;     ;;;;     ;;;    ;;;;;;  ;;;;;;;
;   ;     ;   ; ;   ;    ;   ;  ;   ;     ;    ;   ;   ;   ;     ;    ;   
;   ;     ;   ; ;   ;     ;  ;  ;   ;     ;    ;  ;     ;  ;     ;    ;   
;   ;     ;   ; ;   ;     ;  ;   ; ;      ;       ;     ;  ;     ;    ;   
;   ;;;;;;   ;   ;  ;     ;  ;    ;        ;;;;   ;     ;  ;;;;;;     ;   
;   ;   ;    ;;;;;  ;     ;  ;   ; ;           ;  ;     ;  ;   ;      ;   
;   ;    ;   ;   ;  ;     ;  ;  ;   ;     ;    ;  ;     ;  ;    ;     ;   
;   ;    ;  ;     ; ;    ;   ;  ;   ;     ;    ;   ;   ;   ;    ;     ;   
;   ;     ; ;     ; ;;;;;    ; ;     ;     ;;;;     ;;;    ;     ;    ;   
;                                                                         
;                                                                         
;                                                                         

                   
;; vector -> vector
;; Purpose: Sort a vector using radix sort
;; Effect: the vector will be sorted in non-decreasing order.
(define (radix-sort! a-vector)
  (local [(define VECTOR a-vector)
          (define bucket0 (bucket))
          (define bucket1 (bucket))
          (define bucket2 (bucket))
          (define bucket3 (bucket))
          (define bucket4 (bucket))
          (define bucket5 (bucket))
          (define bucket6 (bucket))
          (define bucket7 (bucket))
          (define bucket8 (bucket))
          (define bucket9 (bucket)) 
          (define bucketn1 (bucket))
          (define bucketn2 (bucket))
          (define bucketn3 (bucket))
          (define bucketn4 (bucket))
          (define bucketn5 (bucket))
          (define bucketn6 (bucket))
          (define bucketn7 (bucket))
          (define bucketn8 (bucket))
          (define bucketn9 (bucket))
          ;; --> (void)
          ;; Purpose: Initialize the buckets
          ;; Effect: All the buckets are mutated to an empty vector
          (define (init-buckets!)
            (begin
              ((bucketn1 'init) (vector))
              ((bucketn2 'init) (vector))
              ((bucketn3 'init) (vector))
              ((bucketn4 'init) (vector))
              ((bucketn5 'init) (vector))
              ((bucketn6 'init) (vector))
              ((bucketn7 'init) (vector))
              ((bucketn8 'init) (vector))
              ((bucketn9 'init) (vector))
              ((bucket0 'init) (vector))
              ((bucket1 'init) (vector))
              ((bucket2 'init) (vector))
              ((bucket3 'init) (vector))
              ((bucket4 'init) (vector))
              ((bucket5 'init) (vector))
              ((bucket6 'init) (vector))
              ((bucket7 'init) (vector))
              ((bucket8 'init) (vector))
              ((bucket9 'init) (vector))
              ))
          ;; integer integer -> integer
          ;; Purpose: Return the number at the given place in the input number.
          (define (num-at-place num place)
            (/ (- (remainder num (expt 10 place)) (remainder num (expt 10 (sub1 place)))) (expt 10 (sub1 place))))

          ;; -> (void)
          ; Purpose: Place the digits in VECTOR into buckets organized by the given digits place
          (define (bucketize! digit-place index)
            (if (> index (sub1 (vector-length VECTOR)))
                (void)
                (local
                  [(define to-process (vector-ref VECTOR index))
                   ;; --> void
                   ;; Purpose: Bucktize the current digit at index
                   ;; Effect: The respective bucket is mutated to add the integer at index to the bucket
                   (define (bucketize-one!)
                     (cond
                       [(= (num-at-place to-process digit-place) -1) ((bucketn1 'add) to-process)]
                       [(= (num-at-place to-process digit-place) -2) ((bucketn2 'add) to-process)]
                       [(= (num-at-place to-process digit-place) -3) ((bucketn3 'add) to-process)]
                       [(= (num-at-place to-process digit-place) -4) ((bucketn4 'add) to-process)]
                       [(= (num-at-place to-process digit-place) -5) ((bucketn5 'add) to-process)]
                       [(= (num-at-place to-process digit-place) -6) ((bucketn6 'add) to-process)]
                       [(= (num-at-place to-process digit-place) -7) ((bucketn7 'add) to-process)]
                       [(= (num-at-place to-process digit-place) -8) ((bucketn8 'add) to-process)]
                       [(= (num-at-place to-process digit-place) -9) ((bucketn9 'add) to-process)]  
                       [(= (num-at-place to-process digit-place) 0) ((bucket0 'add) to-process)]
                       [(= (num-at-place to-process digit-place) 1) ((bucket1 'add) to-process)]
                       [(= (num-at-place to-process digit-place) 2) ((bucket2 'add) to-process)]
                       [(= (num-at-place to-process digit-place) 3) ((bucket3 'add) to-process)]
                       [(= (num-at-place to-process digit-place) 4) ((bucket4 'add) to-process)]
                       [(= (num-at-place to-process digit-place) 5) ((bucket5 'add) to-process)]
                       [(= (num-at-place to-process digit-place) 6) ((bucket6 'add) to-process)]
                       [(= (num-at-place to-process digit-place) 7) ((bucket7 'add) to-process)]
                       [(= (num-at-place to-process digit-place) 8) ((bucket8 'add) to-process)]
                       [(= (num-at-place to-process digit-place) 9) ((bucket9 'add) to-process)]
                       ))]
                  (begin
                    (bucketize-one!)
                    (bucketize! digit-place (add1 index)))
                  )
                ))
          ;; --> void
          ;; Pupose: Dump all the buckets into VECTOR
          ;; Effect: VECTOR is mutated to the elements in the bucket starting from -9 to 9 and each bucket is initalized.
          (define (dump-all!)
            (local [(define index1 0)
                    (define index2 0)]
              (begin
                (set! index1 (+ index1 index2))
                (set! index2 ((bucketn9 'size)))
                (set! VECTOR ((bucketn9 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucketn8 'size)))
                (set! VECTOR ((bucketn8 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucketn7 'size)))
                (set! VECTOR ((bucketn7 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucketn6 'size)))
                (set! VECTOR ((bucketn6 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucketn5 'size)))
                (set! VECTOR ((bucketn5 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucketn4 'size)))
                (set! VECTOR ((bucketn4 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucketn3 'size)))
                (set! VECTOR ((bucketn3 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucketn2 'size)))
                (set! VECTOR ((bucketn2 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucketn1 'size)))
                (set! VECTOR ((bucketn1 'dump) VECTOR index1))          
                (set! index1 (+ index1 index2))
                (set! index2 ((bucket0 'size)))
                (set! VECTOR ((bucket0 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucket1 'size)))
                (set! VECTOR ((bucket1 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucket2 'size)))
                (set! VECTOR ((bucket2 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucket3 'size)))
                (set! VECTOR ((bucket3 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucket4 'size)))
                (set! VECTOR ((bucket4 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucket5 'size)))
                (set! VECTOR ((bucket5 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucket6 'size)))
                (set! VECTOR ((bucket6 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucket7 'size)))
                (set! VECTOR ((bucket7 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucket8 'size)))
                (set! VECTOR ((bucket8 'dump) VECTOR index1))
                (set! index1 (+ index1 index2))
                (set! index2 ((bucket9 'size)))
                (set! VECTOR ((bucket9 'dump) VECTOR index1))
                )))
          ;; integer integer -> vector
          ;; Purpose: initialize the buckets, bucketize all the elements in the vector, then dump them back into the vector.
          ;; How: Take in a index of the place which is being processed, and the max integer length. Bucketize by this digits place
          ;;      and recursively call the function by incrementing the digits place by one.
          ;; Accumulator invariant: index = current digits place being sorted by
          ;;                        max-int-len = length of the longest integer in the vector
          ;; Termination argument: This function will always terminate because the index starts out less than the max int length,
          ;;                       and it is incremented by one wiht every recursive call. Therefore it must eventually exceed the
          ;;                       value of max-int-len, at which point the function will terminate.
          (define (init-bucket-dump index max-int-len)
            (if (> index max-int-len)
                VECTOR
                (begin
                  (init-buckets!)
                  (bucketize! index 0)
                  (dump-all!)
                  (init-bucket-dump (add1 index) max-int-len))))
          ]
    
    (begin
      (init-bucket-dump 1 (longest-int-len VECTOR))
      (void))
  
    ))
;; Sample Vectors:
(define Ve1 (vector 3 5 2 4))
(define Ve2 (vector 12 321 4564 87 4523 56))
(define Ve3 (vector 356 409 33 21 4043))   
(define Ve4 (vector 918 82 -87 31 780 103 4))
(define Ve5 (vector -918 -82 -87 31 -780 -103 -4))  
;; Sample Values
(define Ve1s (vector 2 3 4 5))
(define Ve2s (vector 12 56 87 321 4523 4564))
(define Ve3s (vector 21 33 356 409 4043))
(define Ve4s (vector -87 4 31 82 103 780 918))
(define Ve5s (vector -918 -780 -103 -87 -82 -4 31))
;; Tests for Radix Sort
(check-expect (begin (radix-sort! Ve1) Ve1) Ve1s)
(check-expect (begin (radix-sort! Ve2) Ve2) Ve2s)
(check-expect (begin (radix-sort! Ve3) Ve3) Ve3s)
(check-expect (begin (radix-sort! Ve4) Ve4) Ve4s)
(check-expect (begin (radix-sort! Ve5) Ve5) Ve5s)


;                                                                            
;                                                                            
;                                                                            
;     ;;;    ;     ;  ;    ;;;    ;     ;     ;;;;     ;;;    ;;;;;;  ;;;;;;;
;    ;   ;   ;     ;  ;   ;   ;   ;    ;     ;    ;   ;   ;   ;     ;    ;   
;   ;     ;  ;     ;  ;  ;     ;  ;   ;      ;    ;  ;     ;  ;     ;    ;   
;   ;     ;  ;     ;  ;  ;        ;  ;       ;       ;     ;  ;     ;    ;   
;   ;     ;  ;     ;  ;  ;        ; ;         ;;;;   ;     ;  ;;;;;;     ;   
;   ;     ;  ;     ;  ;  ;        ;; ;            ;  ;     ;  ;   ;      ;   
;   ;  ;; ;  ;     ;  ;  ;     ;  ;   ;      ;    ;  ;     ;  ;    ;     ;   
;    ;   ;    ;   ;   ;   ;   ;   ;    ;     ;    ;   ;   ;   ;    ;     ;   
;     ;;; ;    ;;;    ;    ;;;    ;     ;     ;;;;     ;;;    ;     ;    ;   
;                                                                            
;                                                                            
;                                                                            


;; (vectorof number) → (void)
;; Purpose: Sort the given vector in nondecreasing order
;; Effect: Vector elements are rearranged in place in
;; nondecreasing order
(define (qs-in-place! V)
  (local [ ;; natnum natnum → (void)
          ;; Purpose: Swap the elements at the given indices
          ;; Effect: V is mutated by swapping elements at given indices
          (define (swap! i j)
            (local [(define temp (vector-ref V i))]
              (begin
                (vector-set! V i (vector-ref V j))
                (vector-set! V j temp))))
          
          ;; number [int int] → natnum
          ;; Purpose: Find the largest index, i, such that
          ;; V[i] ≤ to the given pivot
          ;; Assumption: V[low] = pivot
          (define (find<= pivot low high)
            (if (or (> low high)
                    (<= (vector-ref V high) pivot))
                high
                (find<= pivot low (sub1 high))))
          
          ;; number [int int] → natnum
          ;; Purpose: If it exists, find smallest index ≥ low,
          ;; i, such that V[i] > given pivot if it exists.
          ;; Otherwise, return a value greater than high.
          (define (find> pivot low high)
            (if (or (> low high)
                    (> (vector-ref V low) pivot))
                low
                (find> pivot (add1 low) high)))

          ;; number [int int] → natnum
          ;; Purpose: Return the position of the pivot in the
          ;; sorted V
          ;; How: The smallest index of a vector element > pivot
          ;; and the largest index of an element <= to the
          ;; pivot are found. If they form an empty vector
          ;; interval the largest index of an element <= to
          ;; the pivot is returned. Otherwise, the two
          ;; indexed values are swapped and the partitioning
          ;; process continues with the vector interval
          ;; formed by the two indices.
          ;; Effect: V’s elements are rearranged so that all
          ;; elements <= to the pivot are at the beginning
          ;; of the vector interval and all elements > the
          ;; pivot are at the end of the vector interval.
          (define (partition! pivot low high)
            (local [(define first>pivot (find> pivot low high))
                    (define first<=pivot (find<= pivot low high))]
              (if (> first>pivot first<=pivot)
                  first<=pivot
                  (begin
                    (swap! first>pivot first<=pivot)
                    (partition! pivot
                                first>pivot
                                first<=pivot)))))
          ;; Termination Argument
          ;; Every recursive call is made with a smaller vector
          ;; interval that does not contain the beginning numbers
          ;; <= to the pivot and the ending numbers > pivot.
          ;; Eventually, the recursive call is made with an empty
          ;; vector interval and the function halts.
          
          ;; [int int] → (void)
          ;; Purpose: Sort V’s elements in the given vector interval
          ;; in nondecreasing order
          ;; How: The vector is partitioned in two. The first element
          ;; is placed in the vector position between the
          ;; elements ≤ to it and the elements > than it. The
          ;; The vector intervals for the two parts of the
          ;; partition are recursively sorted
          ;; Effect: Vector elements in the given vector interval are
          ;; rearranged in nondecreasing order.
          (define (qs-aux! low high)
            (if (> low high)
                (void)
                (local [(define pivot (vector-ref V low))
                        (define pivot-pos (partition! pivot low high))]
                  (begin
                    (swap! low pivot-pos)
                    (qs-aux! low (sub1 pivot-pos))
                    (qs-aux! (add1 pivot-pos) high)))))
          ;; Termination Argument
          ;; A given nonempty vector interval is divided into two
          ;; smaller vector intervals and these are recursively
          ;; processed. Eventually, the given vector interval
          ;; becomes empty and the function halts.
          ]
(qs-aux! 0 (sub1 (vector-length V)))))

;; Sample Vectors:
(set! Ve1 (vector 3 5 2 4))
(set! Ve2 (vector 12 321 4564 87 4523 56))
(set! Ve3 (vector 356 409 33 21 4043))   
(set! Ve4 (vector 918 82 -87 31 780 103 4))
(set! Ve5 (vector -918 -82 -87 31 -780 -103 -4))  

;; Tests for Quick Sort
(check-expect (begin (qs-in-place! Ve1) Ve1) Ve1s)
(check-expect (begin (qs-in-place! Ve2) Ve2) Ve2s)
(check-expect (begin (qs-in-place! Ve3) Ve3) Ve3s)
(check-expect (begin (qs-in-place! Ve4) Ve4) Ve4s)
(check-expect (begin (qs-in-place! Ve5) Ve5) Ve5s)


;                                                                      
;                                                                      
;                                                                      
;   ;     ;  ;;;;;;    ;    ;;;;;       ;;;;     ;;;    ;;;;;;  ;;;;;;;
;   ;     ;  ;        ; ;   ;    ;     ;    ;   ;   ;   ;     ;    ;   
;   ;     ;  ;        ; ;   ;    ;     ;    ;  ;     ;  ;     ;    ;   
;   ;     ;  ;        ; ;   ;    ;     ;       ;     ;  ;     ;    ;   
;   ;;;;;;;  ;;;;;;  ;   ;  ;;;;;       ;;;;   ;     ;  ;;;;;;     ;   
;   ;     ;  ;       ;;;;;  ;               ;  ;     ;  ;   ;      ;   
;   ;     ;  ;       ;   ;  ;          ;    ;  ;     ;  ;    ;     ;   
;   ;     ;  ;      ;     ; ;          ;    ;   ;   ;   ;    ;     ;   
;   ;     ;  ;;;;;; ;     ; ;           ;;;;     ;;;    ;     ;    ;   
;                                                                      
;                                                                      
;                                                                      

;; (vectorof number) → (void)
;; Purpose: Sort the given vector in nondecreasing order
;; Effect: The given vector’s elements are rearranged in
;; nondecreasing order
(define (heap-sort-in-place! V)
  (local [;; natnum natnum → (void)
          ;; Purpose: Swap the elements at the given
          ;; indices
          ;; Effect: V is mutated by swapping elements at
          ;; given indices
          (define (swap! i j)
            (local [(define temp (vector-ref V i))]
              (begin
                (vector-set! V i (vector-ref V j))
                (vector-set! V j temp))))
          ;; natnum → natnum
          ;; Purpose: Return the index for the right
          ;; subheap’s root
          (define (right-heap-root parent-index)
            (+ (* 2 parent-index) 2))
          ;; natnum → natnum
          ;; Purpose: Return the index for the left
          ;; subhead’s root
          (define (left-heap-root parent-index)
            (add1 (* 2 parent-index)))
          ;; natnum → natnum
          ;; Purpose: Return the parent index in the heap
          ;; Assumption: the given index is in
          ;; [1..(sub1 (vector-length V))]
          (define (parent i)
            (if (even? i)
                (quotient (sub1 i) 2)
                (quotient i 2)))
          ;; trickle-down!: [int int] → (void)
          ;; Purpose: For the given VINTV, reestablish a heap
          ;; rooted at low
          ;; Effect: Vector elements are rearranged to have
          ;; a heap rooted at low
          ;; Assumption: V[low+1..high] are all heap roots
          (define (trickle-down! low high)
            (local
              [(define rc-index (right-heap-root low))
               (define lc-index (left-heap-root low))]
              (cond [(> lc-index high) (void)];; root has no children
                    [(> rc-index high) ;; root only has a left child
                     (if (<= (vector-ref V lc-index)
                             (vector-ref V low))
                         (void)
                         (begin
                           (swap! low lc-index)
                           (trickle-down! lc-index high)))]
                    [else ;; root has two children
                     (local
                       [(define mc-index (if (>= (vector-ref V lc-index)
                                                 (vector-ref V rc-index))
                                             lc-index
                                             rc-index))]
                       (cond [(>= (vector-ref V low)
                                  (vector-ref V mc-index))
                              (void)]
                             [else (begin
                                     (swap! low mc-index)
                                     (trickle-down! mc-index high))]))])))
           #| Termination Argument:
            A recursive call is only made when V[low] has one or two children.
            That is, the index of any child must be less than or equal to high.
            Every recursive call is made with an interval formed by a child index
            and high. Eventually, the given vector interval becomes empty or V[low]
            is a heap root and the mutator terminates|#
          
          ;; [int int] → (void)
          ;; Purpose: For the given VINTV, sort the vector elements
          ;; Effect: V’s elements in the given VINTV are rearranged
          ;; in nondecreasing order
          ;; Assumption: V[low..high] is a heap
          (define (sorter! low high)
            (cond [(> low high) (void)]
                  [else (begin
                          (swap! low high)
                          (trickle-down! low (sub1 high))
                          (sorter! low (sub1 high)))]))
          ;; heapify!: [int int] → (void)
          ;; Purpose: Transform the elements in the given VINTV
          ;; into a heap
          ;; Effect: Rearrange the vector elements to form a heap
          ;; rooted at low
          ;; Assumptions:
          ;; low > 0 Given VINTV is valid for V
          ;;
          ;; Given VINTV is valid for V
          ;;
          ;; Elements indexed in [high+1..(sub1 (vector-length V))]
          ;; are heap roots
          (define (heapify! low high)
            (cond [(> low high) (void)]
                  [else
                   (local [(define parent-index (parent high))]
                     (cond [(>= (vector-ref V parent-index)
                                (vector-ref V high))
                            (heapify! low (sub1 high))]
                           [else
                            (begin
                              (swap! parent-index high)
                              (trickle-down! high
                                             (sub1 (vector-length V)))
                              (heapify! low (sub1 high)))]))]))
          ]
    (begin
      (heapify! 1 (sub1 (vector-length V)))
      (sorter! 0 (sub1 (vector-length V))))))

;; Sample Vectors:
(set! Ve1 (vector 3 5 2 4))
(set! Ve2 (vector 12 321 4564 87 4523 56))
(set! Ve3 (vector 356 409 33 21 4043))   
(set! Ve4 (vector 918 82 -87 31 780 103 4))
(set! Ve5 (vector -918 -82 -87 31 -780 -103 -4))  

;; Tests for Heap Sort
(check-expect (begin (heap-sort-in-place! Ve1) Ve1) Ve1s)
(check-expect (begin (heap-sort-in-place! Ve2) Ve2) Ve2s)
(check-expect (begin (heap-sort-in-place! Ve3) Ve3) Ve3s)
(check-expect (begin (heap-sort-in-place! Ve4) Ve4) Ve4s)
(check-expect (begin (heap-sort-in-place! Ve5) Ve5) Ve5s)


;                                               
;                                               
;                                               
;   ;  ;     ;   ;;;;     ;;;    ;;;;;;  ;;;;;;;
;   ;  ;;    ;  ;    ;   ;   ;   ;     ;    ;   
;   ;  ; ;   ;  ;    ;  ;     ;  ;     ;    ;   
;   ;  ; ;   ;  ;       ;     ;  ;     ;    ;   
;   ;  ;  ;  ;   ;;;;   ;     ;  ;;;;;;     ;   
;   ;  ;   ; ;       ;  ;     ;  ;   ;      ;   
;   ;  ;   ; ;  ;    ;  ;     ;  ;    ;     ;   
;   ;  ;    ;;  ;    ;   ;   ;   ;    ;     ;   
;   ;  ;     ;   ;;;;     ;;;    ;     ;    ;   
;                                               
;                                               
;                                               

;; (vectorof number) -> (vectorof number)
;; Purpose: Sort the given vector in nondecreasing order
;; Effect: Vector elements are rearranged in place in
;; nondecreasing order 
(define (is-in-place! V)
  (local [ ;; natnum natnum → (void)
          ;; Purpose: Swap the elements at the given indices
          ;; Effect: V is mutated by swapping elements at given indices
          (define (swap! i j)
            (local [(define temp (vector-ref V i))]
              (begin
                (vector-set! V i (vector-ref V j))
                (vector-set! V j temp))))       
          ;; vector-index -> (vectorof number)
          ;; Purpose: Sorts every number at every index of the given vector. 
          ;; How: The function inserts the number at the given vector-index to the sorted portion of the vector
          ;;      (0 ... (sub1 vector-index)) in nondecreasing order.
          ;; Termination Argument: Assuming that the insert! auxiliary function works correctly,
          ;;                       1 will be added to the vector-index every time insertion-sorting! is processed
          ;;                       recursively. Eventually the given vector-index will be greather than the valid
          ;;                       indices for the given vector (sub1 (vector-length V)) and the function will terminate.
          ;; Accumulator Invarient: vector-index: The index of the number in the vector which is being processed.
          ;; Assumption: Vector is not empty
          (define (insertion-sorting! vector-index)
            (local [;; vector-index vector-index -> (void)
                    ;; Purpose: Inserts the number at given index1 in the sorted portion of the given
                    ;;          vector (indices 0 to (sub1 index1)) in non-decreasing order. 
                    ;; How: Compares number at given index1 with
                    ;;      number at given index2 and swaps them if the
                    ;;      number at the given index1 is less than
                    ;;      the number at given index2. This process occurs recursively
                    ;;      with subtracting 1 from both index1 and index2 at each iteration until index 2
                    ;;      is less than 0 or the number at given index1 is greater than the number
                    ;;      at given index2.
                    ;; Termination Argument: Eventually index2 will be subtracted to less than 0 or
                    ;;                       the number at index1 will be greater than the number at index2,
                    ;;                       for which the insertion-sorting! function will be called.
                    ;; Assumption: Numbers at indices (0 ... index2) in the given vector are sorted in nondecreasing order.
                    (define (insert! index1 index2)
                      (cond 
                        [(< index2 0)
                         (insertion-sorting! (add1 vector-index));)
                         ]
                        [(> (vector-ref V index2) (vector-ref V index1))                         
                         (begin
                           (swap! index1 index2)
                           (insert! (sub1 index1) (sub1 index2)))]
                        [else (insertion-sorting! (add1 vector-index))]))]
              (if (> vector-index (sub1 (vector-length V)))
                  V
                  (insert! vector-index (sub1 vector-index)))))]
    (if (= (vector-length V) 0)
        (vector)
   
        (insertion-sorting! 1)))) 



;; Sample Vectors:
(set! Ve1 (vector 3 5 2 4))
(set! Ve2 (vector 12 321 4564 87 4523 56))
(set! Ve3 (vector 356 409 33 21 4043))   
(set! Ve4 (vector 918 82 -87 31 780 103 4))
(set! Ve5 (vector -918 -82 -87 31 -780 -103 -4))  

;; Tests for Insertion Sort
(check-expect (begin (is-in-place! Ve1) Ve1) Ve1s)
(check-expect (begin (is-in-place! Ve2) Ve2) Ve2s)
(check-expect (begin (is-in-place! Ve3) Ve3) Ve3s)
(check-expect (begin (is-in-place! Ve4) Ve4) Ve4s)
(check-expect (begin (is-in-place! Ve5) Ve5) Ve5s)

;; natnum (listof ((vectorof number) → (void))) → (void)
;; Purpose: Run empirical study with vectors that have lengths
;; that are multiples of 1000 in [1000..natnum*1000]
(define (empirical-study factor lst-of-sorters) 
  (local
    [(define NUM-RUNS 5)
     (define V (build-vector (* factor 500) (λ (i) (random 10000000))))
     ;; (vectorof number) natnum (listof ((vectorof number) → (void)))
     ;; → (void)
     ;; Purpose: Time the given in-place sorters using the given vector
     ;; the given number of times
     (define (run-experiments V runs sorters)
       (local [;; (listof ((vectorof number)→(void)))→(void)
               ;; Purpose: Run n experiments
               (define (run sorters)
                 (if (empty? sorters)
                     (void)
                     (local [;; (vectorof number)
                             ;; Purpose: Copy of V to sort
                             (define V1 (build-vector
                                         (vector-length V)
                                         (λ (i) (vector-ref V i))))]
                       (begin
                         (display (format "Sorter ~s: "
                                          (add1 (- (length lst-of-sorters)
                                                   (length sorters)))))
                         (time ((first sorters) V1))
                         (run (rest sorters))))))]
         (if (= runs 0)
             (void)
             (begin
               (display (format " RUN ~s\n" (add1 (- NUM-RUNS runs))))
               (run sorters)
               (run-experiments V (sub1 runs) sorters)))))]
    (if (= factor 0)
        (void)
        (begin
          (display (format "Experiments for length ~s \n" (* factor 500)))
          (run-experiments V NUM-RUNS lst-of-sorters)
          (newline)
          (newline)
          (empirical-study (sub1 factor) lst-of-sorters)))))

(define SORTERS (list radix-sort! qs-in-place! heap-sort-in-place!
                 is-in-place!))

(empirical-study 40 SORTERS)



   
