using Business.Interfaces;
using Dtos.GRPCData;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace UI.Controllers {

    [AutoValidateAntiforgeryToken]
    [Authorize(Roles = "Member")]
    public class TennisController : Controller {


        private readonly ITennisService _tennisService;
        public TennisController(ITennisService tennisService) {
            _tennisService = tennisService;
        }


        [HttpPost]
        public async Task<IActionResult> GenerateProcess(GenerateProcessModel model) {
            var response = await _tennisService.Create(model);
            return RedirectToAction("Index", "Process", new { @id = model.SessionId });
        }


        [HttpGet]
        public async Task<IActionResult> CalculateTotalScore(long sessionId) {
            var response = await _tennisService.CalculateTotalScore(sessionId);
            return RedirectToAction("Index", "PlayingDatum");
        }


    }
}