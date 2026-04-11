(require 2htdp/universe)
(require 2htdp/image)

(define IMG-WDTH 30)
(define IMG-HGHT 30)

(define MAX-CHRS-HOR 8)
(define MAX-CHRS-VER 10)

(define ESCN-CLR 'pink)
(define ESCN2-CLR 'black)

(define ESCN-W (* MAX-CHRS-HOR IMG-WDTH))
(define ESCN-H (* MAX-CHRS-VER IMG-HGHT))

(define E-SCENE (empty-scene ESCN-W ESCN-H ESCN-CLR))
(define E-SCENE2 (empty-scene ESCN-W ESCN-H ESCN2-CLR))


(define (IS-CI img) (and (<= (image-width (circle 10 'solid 'red)) IMG-WDTH)
                         (<= (image-height (circle 10 'solid 'red)) IMG-HGHT)))
(define (NOT-CI img) (and (<= (image-width (square 40 'solid 'blue)) IMG-WDTH)
                          (<= (image-height (square 40 'solid 'blue)) IMG-HGHT)))

(define (NOT-CI2 img) (and (<= (image-width (rectangle 2 50 'solid 'blue)) IMG-WDTH)
                           (<= (image-height (rectangle 2 50 'solid 'blue)) IMG-HGHT)))

(define WINDOW-COLOR 'darkgray)
(define WINDOW2-COLOR 'white)

(define WINDOW (ellipse 3 10 'solid WINDOW-COLOR))
(define WINDOW2 (ellipse 3 10 'solid WINDOW2-COLOR))

(define (mk-window-img a-color)(ellipse 3 10 'solid a-color))

(check-expect (mk-window-img WINDOW-COLOR) WINDOW)
(check-expect (mk-window-img WINDOW2-COLOR) WINDOW2)

(check-expect (mk-window-img WINDOW-COLOR) .)
(check-expect (mk-window-img WINDOW2-COLOR) .)


(define (mk-fuselage-img a-color)(circle (* 1/3 IMG-HGHT) 'solid a-color))

(define FUSELAGE-COLOR 'green)
(define FUSELAGE2-COLOR 'blue)

(define FUSELAGE (circle (* 1/3 IMG-HGHT) 'solid FUSELAGE-COLOR))
(define FUSELAGE2 (circle (* 1/3 IMG-HGHT) 'solid FUSELAGE2-COLOR))

(check-expect (mk-fuselage-img FUSELAGE-COLOR) FUSELAGE)
(check-expect (mk-fuselage-img FUSELAGE2-COLOR) FUSELAGE2)

(check-expect (mk-fuselage-img FUSELAGE-COLOR) .)
(check-expect (mk-fuselage-img FUSELAGE2-COLOR) .)


(define (mk-single-booster-img a-color)(rotate 180 (triangle (/ (image-width FUSELAGE) 2) 'solid a-color)))

(define NACELLE-COLOR 'red)
(define NACELLE2-COLOR 'black)

(define SINGLE-BOOSTER (rotate 180 (triangle (/ (image-width FUSELAGE) 2) 'solid NACELLE-COLOR)))
(define SINGLE-BOOSTER2 (rotate 180 (triangle (/ (image-width FUSELAGE) 2) 'solid NACELLE2-COLOR)))

(check-expect (mk-single-booster-img NACELLE-COLOR) SINGLE-BOOSTER)
(check-expect (mk-single-booster-img NACELLE2-COLOR)SINGLE-BOOSTER2)

(check-expect (mk-single-booster-img NACELLE-COLOR) .)
(check-expect (mk-single-booster-img NACELLE2-COLOR) .)


(define (mk-booster-img a-sb-img)(beside a-sb-img a-sb-img))
(define BOOSTER (beside SINGLE-BOOSTER SINGLE-BOOSTER))
(define BOOSTER2 (beside SINGLE-BOOSTER2 SINGLE-BOOSTER2))

(check-expect (mk-booster-img SINGLE-BOOSTER) BOOSTER)
(check-expect (mk-booster-img SINGLE-BOOSTER2) BOOSTER2)


(define (mk-rocket-main-img a-window a-fuselage a-booster)
  (place-image a-window(/ (image-width a-fuselage) 2)(/ (image-height a-fuselage) 4)(above a-fuselage a-booster)))

(define ROCKET-MAIN(place-image WINDOW(/ (image-width FUSELAGE) 2)(/ (image-height FUSELAGE) 4)(above FUSELAGE BOOSTER)))
(define ROCKET-MAIN2(place-image WINDOW2(/ (image-width FUSELAGE2) 2)(/ (image-height FUSELAGE2) 4)(above FUSELAGE2 BOOSTER2)))

(check-expect (mk-rocket-main-img WINDOW FUSELAGE BOOSTER)ROCKET-MAIN)
(check-expect (mk-rocket-main-img WINDOW2 FUSELAGE2 BOOSTER2)ROCKET-MAIN2)


(define (mk-nacelle-img a-rocket-main-img a-color)(rectangle (image-width a-rocket-main-img)(/ (image-height a-rocket-main-img) 4)'solida-color))

(define NACELLE (rectangle (image-width ROCKET-MAIN)(/ (image-height ROCKET-MAIN) 4) 'solid NACELLE-COLOR))
(define NACELLE2 (rectangle (image-width ROCKET-MAIN2)(/ (image-height ROCKET-MAIN2) 4) 'solid NACELLE2-COLOR))


(define (mk-rocket-ci a-rocket-main-img a-nacelle-img)
  (place-image a-nacelle-img(/ (image-width a-rocket-main-img) 2)(* 0.7 (image-height a-rocket-main-img))a-rocket-main-img))
  
(define ROCKET-IMG (place-image NACELLE (/ (image-width ROCKET-MAIN) 2)(* 0.7 (image-height ROCKET-MAIN))ROCKET-MAIN))
(define ROCKET-IMG2 (place-image NACELLE2(/ (image-width ROCKET-MAIN2) 2)(* 0.7 (image-height ROCKET-MAIN2))ROCKET-MAIN2))

(check-expect (mk-rocket-ci ROCKET-MAIN NACELLE) ROCKET-IMG)
(check-expect (mk-rocket-ci ROCKET-MAIN2 NACELLE2) ROCKET-IMG2)
(check-expect (IS-CI ROCKET-IMG) #true)
(check-expect (IS-CI ROCKET-IMG2) #true)




(define ALIEN-IMG (overlay (circle 5 'solid 'black)
                           (circle 10 'solid 'blue)
                           (circle 15 'solid 'white)))

;; Constants
(define MIN-IMG-X 0)
(define MAX-IMG-X (sub1 MAX-CHRS-HOR))
(define MIN-IMG-Y 0)
(define MAX-IMG-Y (sub1 MAX-CHRS-VER))
(define MY-NAME "C")

;; Contants for INIT-WORLD
(define AN-IMG-X (/ MAX-CHRS-HOR 2))
(define INIT-ROCKET (make-posn AN-IMG-X MAX-IMG-Y))
(define INIT-ROCKET2 (make-posn 5 5))



;;ALIEN

(define-struct alien (pos spd dir))

(define INIT-ALIEN1 (make-alien (make-posn AN-IMG-X (* .75 MAX-IMG-Y)) 1 'right))
(define INIT-ALIEN2 (make-alien (make-posn MIN-IMG-X (* .5 MAX-IMG-Y)) 2 'right))
(define INIT-ALIEN3 (make-alien (make-posn MAX-IMG-X (* .25 MAX-IMG-Y)) 3 'left))

;;WORLD

(define-struct world (rocket alien1 alien2 alien3))

(define INIT-WORLD (make-world INIT-ROCKET INIT-ALIEN1 INIT-ALIEN2 INIT-ALIEN3))

;;UNIVERSE
(define-struct univ (iws game))

(define OTHR-UNIV  (make-univ (list iworld1 iworld2) INIT-WORLD))

;;processing keys
(define (move-rckt-right a-rocket)
  (if (< (posn-x a-rocket) (sub1 MAX-CHRS-HOR))
      (make-posn(+ (posn-x a-rocket) .05)(posn-y a-rocket))
      a-rocket))


(define (move-rckt-left a-rocket)
  (if (> (posn-x a-rocket) 0)
      (make-posn(- (posn-x a-rocket) .05)(posn-y a-rocket))
      a-rocket))

      


(define (process-key a-world a-key)
  (cond [(key=? a-key "right")
         (make-world (move-rckt-right (world-rocket a-world))
                     (world-alien1 a-world)
                     (world-alien2 a-world)
                     (world-alien3 a-world))]
        [(key=? a-key "left")
         (make-world (move-rckt-left (world-rocket a-world))
                     (world-alien1 a-world)
                     (world-alien2 a-world)
                     (world-alien3 a-world))]
        [(key=? a-key " ")
         (make-world (world-rocket a-world)
                     (world-alien1 a-world)
                     (world-alien2 a-world)
                     (world-alien3 a-world))]
        [else a-world]))


;auxillary for process-tick




(define (move-right-image-x an-alien)
  (+ (posn-x (alien-pos an-alien)) (* .1 (alien-spd an-alien))))

(define (move-left-image-x an-alien)
  (- (posn-x (alien-pos an-alien)) (* .1 (alien-spd an-alien))))


(define (move-alien an-alien)(if
                              (eq? (alien-dir an-alien)'right)
                              (make-posn (move-right-image-x an-alien) (posn-y (alien-pos an-alien)))
                              (make-posn (move-left-image-x an-alien) (posn-y (alien-pos an-alien)))
                              ))

(define (alien-at-right-edge? an-alien)
  (and (<= (posn-x (alien-pos an-alien)) MAX-IMG-X)
       (>= (posn-x (alien-pos an-alien)) (- MAX-IMG-X .4))
       )
  )

(define (alien-at-left-edge? an-alien)
  (and (<= (posn-x (alien-pos an-alien)) (+ MIN-IMG-X .4))
       (>= (posn-x (alien-pos an-alien)) MIN-IMG-X)
       )
  )


(define (new-dir an-alien)
  (cond [(alien-at-left-edge? an-alien) 'right]
        [(alien-at-right-edge? an-alien) 'left]
        [else (alien-dir an-alien)]))



(define (move-rckt-up a-rocket)
  (make-posn(posn-x a-rocket)(- (posn-y a-rocket) .075)))



(define (hit? a-world)
  (cond
    [(and (and (> (posn-x (world-rocket a-world)) (sub1 (posn-x (alien-pos (world-alien1 a-world)))))
               (< (posn-x (world-rocket a-world)) (add1 (posn-x (alien-pos (world-alien1 a-world))))))
          (and (> (posn-y (world-rocket a-world)) (sub1 (posn-y (alien-pos (world-alien1 a-world)))))
               (< (posn-y (world-rocket a-world)) (add1 (posn-y (alien-pos (world-alien1 a-world)))))))
     (make-posn (random MAX-IMG-X) MAX-IMG-Y)]
    [(and (and (> (posn-x (world-rocket a-world)) (sub1 (posn-x (alien-pos (world-alien2 a-world)))))
               (< (posn-x (world-rocket a-world)) (add1 (posn-x (alien-pos (world-alien2 a-world))))))
          (and (> (posn-y (world-rocket a-world)) (sub1 (posn-y (alien-pos (world-alien2 a-world)))))
               (< (posn-y (world-rocket a-world)) (add1 (posn-y (alien-pos (world-alien2 a-world)))))))
     (make-posn (random MAX-IMG-X) MAX-IMG-Y)]
    [(and (and (> (posn-x (world-rocket a-world)) (sub1 (posn-x (alien-pos (world-alien3 a-world)))))
               (< (posn-x (world-rocket a-world)) (add1 (posn-x (alien-pos (world-alien3 a-world))))))
          (and (> (posn-y (world-rocket a-world)) (sub1 (posn-y (alien-pos (world-alien3 a-world)))))
               (< (posn-y (world-rocket a-world)) (add1 (posn-y (alien-pos (world-alien3 a-world)))))))
     (make-posn (random MAX-IMG-X) MAX-IMG-Y)]
    [else (move-rckt-up(world-rocket a-world))]
    ))
 
;;Processing ticks
(define (process-tick a-world)
  (make-world 
   (hit? a-world)
   (make-alien (move-alien (world-alien1 a-world))
               (alien-spd (world-alien1 a-world))
               (new-dir (world-alien1 a-world)))
   (make-alien (move-alien (world-alien2 a-world))
               (alien-spd (world-alien2 a-world))
               (new-dir (world-alien2 a-world)))
   (make-alien (move-alien (world-alien3 a-world))
               (alien-spd (world-alien3 a-world))
               (new-dir (world-alien3 a-world)))
   ))
                         
 
 
; draw world

(define (image-x->pix-x ix)(+ (* ix IMG-WDTH) (/ IMG-WDTH 2)))

(define (image-y->pix-y iy)(+ (* iy IMG-HGHT) (/ IMG-HGHT 2)))

(define (draw-ci char-img an-img-x an-img-y scn)(place-image char-img (image-x->pix-x an-img-x) (image-y->pix-y an-img-y) scn))

(define (draw-alien an-alien scn)(draw-ci ALIEN-IMG (posn-x (alien-pos an-alien)) (posn-y (alien-pos an-alien)) scn))

(define (draw-rocket a-rocket scn)(draw-ci ROCKET-IMG (posn-x a-rocket)(posn-y a-rocket) scn))

(define (draw-world a-world )
  (draw-alien (world-alien1 a-world)
              (draw-alien (world-alien2 a-world)
                          (draw-alien (world-alien3 a-world)
                                      (draw-rocket (world-rocket a-world) E-SCENE)))))




; game over

(define (game-over? a-world)
  (<= (posn-y (world-rocket a-world)) MIN-IMG-Y))

(define (draw-final-world a-world)
  (place-image (text "YOU HAVE ESCAPED!" 20 'olive)
                      (/ ESCN-W 2) (/ ESCN-H 2) (draw-world a-world)))




(define TICK-RATE .1)

(define (run a-name)
  
  (big-bang INIT-WORLD
    [to-draw draw-world]
    [name a-name]
    [on-key process-key]
    [on-tick process-tick TICK-RATE]
    [stop-when game-over? draw-final-world]))

(run "i")
 
















